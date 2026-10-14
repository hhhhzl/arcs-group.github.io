#!/usr/bin/env python3
"""Build deterministic MDOC publication visuals from the repository's 14 main GIFs.

Run with Pillow installed:
  python3 build_mdoc_overview.py --source /path/to/mdoc --output /path/to/assets

Each source is sampled at its original playback time, with short clips looping
independently. The composite loop is 10.24 s (the longest source duration).
Only horizontal white margins are cropped from the multi-robot figures.
"""

from __future__ import annotations

import argparse
import bisect
import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


WIDTH = 1200
MARGIN = 24
GAP = 16
SINGLE_CARD = (373, 372)
MULTI_CARD = (276, 310)
SINGLE_TOP = 84
MULTI_HEADING_TOP = 870
MULTI_TOP = 926
HEIGHT = 1584
BG = "#ffffff"
BORDER = "#dce4ed"
INK = "#153046"
SUBTLE = "#526776"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


@dataclass
class Animation:
    label: str
    agents: int
    path: Path
    frames: list[Image.Image]
    ends: list[int]
    duration: int
    original_size: tuple[int, int]
    crop: tuple[int, int, int, int] | None

    def at(self, timestamp: int) -> Image.Image:
        index = bisect.bisect_right(self.ends, timestamp % self.duration)
        return self.frames[min(index, len(self.frames) - 1)]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def load_animation(source: Path, folder: str, filename: str, label: str, agents: int) -> Animation:
    path = source / "assets/vis/gifs" / folder / filename
    original = Image.open(path)
    size = original.size
    crop = (80, 0, 560, 480) if folder == "MDOC-CBS" else None
    target = (254, 254) if crop else (336, 336)
    frames, ends, elapsed = [], [], 0
    for i in range(original.n_frames):
        original.seek(i)
        frame = original.convert("RGB")
        if crop:
            frame = frame.crop(crop)
        frame = frame.resize(target, Image.Resampling.LANCZOS)
        frames.append(frame)
        elapsed += original.info.get("duration", 100)
        ends.append(elapsed)
    return Animation(label, agents, path, frames, ends, elapsed, size, crop)


def source_list(source: Path) -> tuple[list[Animation], list[Animation]]:
    single = [
        load_animation(source, "MDOC", filename, label, 1)
        for filename, label in [
            ("empty_MDOC.gif", "Empty"),
            ("narrow_MDOC.gif", "Narrow"),
            ("random_MDOC.gif", "Random"),
            ("conveyor_MDOC.gif", "Conveyor"),
            ("dropregion_MDOC.gif", "Drop Region"),
            ("tennis_MDOC.gif", "Tennis"),
        ]
    ]
    multi = [
        load_animation(source, "MDOC-CBS", filename, label, agents)
        for filename, label, agents in [
            ("empty_boundary_MDOC-CBS_10.gif", "Empty · Boundary", 10),
            ("empty_circle_MDOC-CBS_10.gif", "Empty · Circle", 10),
            ("random_MDOC-CBS_10.gif", "Random", 10),
            ("conveyor_boundary_MDOC-CBS_10.gif", "Conveyor · Boundary", 10),
            ("conveyor_circle_MDOC-CBS_10.gif", "Conveyor · Circle", 10),
            ("dropregion_boundary_MDOC-CBS_10.gif", "Drop Region", 10),
            ("empty_large_MDOC-CBS_15.gif", "Empty · Large", 15),
            ("empty_extralarge_MDOC-CBS_15.gif", "Empty · Extra Large", 15),
        ]
    ]
    return single, multi


def make_background(single: list[Animation], multi: list[Animation]) -> tuple[Image.Image, list[tuple[Animation, tuple[int, int]]]]:
    im = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(im)
    draw.text((MARGIN, 22), "Single-Robot Planning with MDOC", fill=INK, font=font(31, True))
    draw.text((MARGIN, 59), "6 environments · 1 agent", fill=SUBTLE, font=font(17))
    placements = []
    for i, animation in enumerate(single):
        x = MARGIN + (i % 3) * (SINGLE_CARD[0] + GAP)
        y = SINGLE_TOP + (i // 3) * (SINGLE_CARD[1] + GAP)
        draw.rounded_rectangle((x, y, x + SINGLE_CARD[0], y + SINGLE_CARD[1]), radius=12, fill=BG, outline=BORDER, width=1)
        draw.text((x + 16, y + 13), animation.label, fill=INK, font=font(20, True))
        draw.text((x + SINGLE_CARD[0] - 74, y + 16), "1 agent", fill=SUBTLE, font=font(15))
        placements.append((animation, (x + 18, y + 34)))

    draw.line((MARGIN, 851, WIDTH - MARGIN, 851), fill=BORDER, width=1)
    draw.text((MARGIN, MULTI_HEADING_TOP), "Multi-Robot Planning with MDOC-CBS", fill=INK, font=font(31, True))
    draw.text((MARGIN, MULTI_HEADING_TOP + 37), "8 scenarios · 10–15 agents", fill=SUBTLE, font=font(17))
    for i, animation in enumerate(multi):
        x = MARGIN + (i % 4) * (MULTI_CARD[0] + GAP)
        y = MULTI_TOP + (i // 4) * (MULTI_CARD[1] + GAP)
        draw.rounded_rectangle((x, y, x + MULTI_CARD[0], y + MULTI_CARD[1]), radius=12, fill=BG, outline=BORDER, width=1)
        draw.text((x + 12, y + 11), animation.label, fill=INK, font=font(18, True))
        draw.text((x + 12, y + 34), f"{animation.agents} agents", fill=SUBTLE, font=font(15))
        placements.append((animation, (x + 11, y + 54)))
    return im, placements


def render(timestamp: int, background: Image.Image, placements: list[tuple[Animation, tuple[int, int]]]) -> Image.Image:
    im = background.copy()
    for animation, xy in placements:
        im.paste(animation.at(timestamp), xy)
    return im


def make_thumbnail(multi: list[Animation], output: Path) -> None:
    im = Image.new("RGB", (1200, 800), BG)
    draw = ImageDraw.Draw(im)
    draw.text((42, 32), "MDOC", fill=INK, font=font(58, True))
    draw.text((44, 105), "Model-Based Diffusion Optimal Control", fill=INK, font=font(34, True))
    draw.text((44, 151), "for Multi-Robot Motion Planning", fill=INK, font=font(34, True))
    selections = [multi[2], multi[4]]
    for index, animation in enumerate(selections):
        x = 34 + index * 570
        y = 230
        draw.rounded_rectangle((x, y, x + 556, y + 518), radius=14, fill=BG, outline=BORDER, width=2)
        draw.text((x + 22, y + 20), animation.label, fill=INK, font=font(28, True))
        draw.text((x + 22, y + 57), f"MDOC-CBS · {animation.agents} agents", fill=SUBTLE, font=font(21))
        # Use a late, converged frame and the same verified content-preserving crop.
        original = Image.open(animation.path)
        original.seek(bisect.bisect_right(animation.ends, animation.duration - 200))
        frame = original.convert("RGB")
        if animation.crop:
            frame = frame.crop(animation.crop)
        frame = frame.resize((432, 432), Image.Resampling.LANCZOS)
        im.paste(frame, (x + 62, y + 82))
    draw.text((44, 766), "Zhilin He · Yorai Shaoul · Jiaoyang Li  |  RSS 2026", fill=SUBTLE, font=font(20))
    im.save(output / "mdoc-thumbnail.jpg", quality=91, optimize=True, subsampling=0)
    im.save(output / "mdoc-thumbnail-preview.png", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    single, multi = source_list(args.source)
    background, placements = make_background(single, multi)
    duration = max(a.duration for a in single + multi)
    # GIF stores delays in 10 ms units: alternate 120/130 ms around the 8 fps
    # sampling interval, preserving the original overall playback speed.
    timestamps = [round(i * 125 / 10) * 10 for i in range((duration + 124) // 125)]
    delays = [b - a for a, b in zip(timestamps, timestamps[1:] + [duration])]

    # Shared palette prevents changing line/background colors between GIF frames.
    palette_samples = [render(t, background, placements).resize((300, 396), Image.Resampling.LANCZOS) for t in (0, 2500, 4900, 7500, 9700)]
    palette_sheet = Image.new("RGB", (1500, 396), BG)
    for i, sample in enumerate(palette_samples):
        palette_sheet.paste(sample, (i * 300, 0))
    adaptive = palette_sheet.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    # Reserve the source plots' categorical colors. Without these reserved
    # entries, the small robot discs can lose saturation in a white-heavy grid.
    semantic_colors = [
        (31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
        (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
        (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
        (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
        (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229),
        (0, 128, 0), (255, 0, 0), (0, 0, 255), (255, 255, 255),
        (0, 0, 0), (21, 48, 70), (82, 103, 118), (220, 228, 237),
        (246, 221, 177), (0, 114, 189), (166, 54, 3), (102, 194, 165),
    ]
    palette_data = adaptive.getpalette()[:96 * 3] + [channel for color in semantic_colors for channel in color]
    palette_data += [255] * (768 - len(palette_data))
    palette = Image.new("P", (1, 1))
    palette.putpalette(palette_data)

    frames = [render(t, background, placements).quantize(palette=palette, dither=Image.Dither.NONE) for t in timestamps]
    gif_path = args.output / "mdoc-overview.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=delays, loop=0, disposal=1, optimize=False)
    for timestamp, filename in [(0, "mdoc-overview-first-frame.png"), (2500, "mdoc-overview-mid-frame.png"), (4900, "mdoc-overview-static.png")]:
        render(timestamp, background, placements).save(args.output / filename, optimize=True)
    make_thumbnail(multi, args.output)

    with Image.open(gif_path) as check:
        actual_frames = check.n_frames
        actual_duration = 0
        for i in range(actual_frames):
            check.seek(i)
            actual_duration += check.info.get("duration", 0)
        # Validate the encoded GIF visually too, rather than only an RGB precursor.
        check.seek(min(39, actual_frames - 1))
        check.convert("RGB").save(args.output / "mdoc-overview-encoded-preview.png", optimize=True)

    metadata = {
        "overview": {"file": gif_path.name, "size": [WIDTH, HEIGHT], "frames": actual_frames, "duration_ms": actual_duration, "loop": "forever", "sampling": "8 fps, with 120/130 ms GIF delays; final sample is 120 ms", "bytes": gif_path.stat().st_size},
        "thumbnail": {"file": "mdoc-thumbnail.jpg", "size": [1200, 800], "bytes": (args.output / "mdoc-thumbnail.jpg").stat().st_size},
        "source_policy": "6 main MDOC GIFs + 8 main MDOC-CBS GIFs. The 2 appendix duplicates are excluded. Source animations play at original speed and loop independently within the 10.24 s overview loop.",
        "sources": [{"file": str(a.path.relative_to(args.source)), "label": a.label, "agents": a.agents, "original_size": a.original_size, "original_frames": len(a.frames), "duration_ms": a.duration, "crop": a.crop} for a in single + multi],
    }
    (args.output / "mdoc-assets-manifest.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: metadata[k] for k in ("overview", "thumbnail")}, indent=2))


if __name__ == "__main__":
    main()
