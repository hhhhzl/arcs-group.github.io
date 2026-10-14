#!/usr/bin/env python3
"""Build an unlabeled, animated MDOC thumbnail from all 14 main demo GIFs.

Requires Pillow. No AI, labels, titles, borders, or geometry redrawing is used.
Run:
  python3 build_mdoc_thumbnail.py --source /path/to/mdoc --output /path/to/assets
"""

from __future__ import annotations

import argparse
import bisect
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


WIDTH, HEIGHT = 480, 560
MASK = (0, 0, 112, 24)
MULTI_CROP = (80, 0, 560, 480)
SOURCES = [
    ("MDOC", "empty_MDOC.gif", "Empty", 1),
    ("MDOC", "narrow_MDOC.gif", "Narrow", 1),
    ("MDOC", "random_MDOC.gif", "Random", 1),
    ("MDOC", "conveyor_MDOC.gif", "Conveyor", 1),
    ("MDOC", "dropregion_MDOC.gif", "Drop Region", 1),
    ("MDOC", "tennis_MDOC.gif", "Tennis", 1),
    ("MDOC-CBS", "empty_boundary_MDOC-CBS_10.gif", "Empty Boundary", 10),
    ("MDOC-CBS", "empty_circle_MDOC-CBS_10.gif", "Empty Circle", 10),
    ("MDOC-CBS", "random_MDOC-CBS_10.gif", "Random", 10),
    ("MDOC-CBS", "conveyor_boundary_MDOC-CBS_10.gif", "Conveyor Boundary", 10),
    ("MDOC-CBS", "conveyor_circle_MDOC-CBS_10.gif", "Conveyor Circle", 10),
    ("MDOC-CBS", "dropregion_boundary_MDOC-CBS_10.gif", "Drop Region", 10),
    ("MDOC-CBS", "empty_large_MDOC-CBS_15.gif", "Empty Large", 15),
    ("MDOC-CBS", "empty_extralarge_MDOC-CBS_15.gif", "Empty Extra Large", 15),
]


def load_sources(source: Path) -> list[dict]:
    animations = []
    for index, (folder, filename, scene, agents) in enumerate(SOURCES):
        path = source / "assets/vis/gifs" / folder / filename
        original = Image.open(path)
        is_single = folder == "MDOC"
        tile_size = 160 if is_single else 120
        frames, ends, elapsed = [], [], 0
        for i in range(original.n_frames):
            original.seek(i)
            frame = original.convert("RGB")
            if is_single:
                # Check the exact source annotation footprint. GIF quantization
                # gives some gray text edges a slight tint, so geometry safety
                # is checked by its known position rather than a color heuristic.
                region = frame.crop(MASK)
                annotation = ImageChops.difference(region, Image.new("RGB", region.size, "white")).convert("L").point(lambda value: 255 if value > 15 else 0).getbbox()
                assert annotation is None or (annotation[0] >= 6 and annotation[1] >= 7 and annotation[2] <= 110 and annotation[3] <= 23), (filename, i, annotation)
                ImageDraw.Draw(frame).rectangle((MASK[0], MASK[1], MASK[2] - 1, MASK[3] - 1), fill="white")
            else:
                # Verify every source frame before removing horizontal white margins.
                difference = ImageChops.difference(frame, Image.new("RGB", frame.size, "white"))
                content = difference.convert("L").point(lambda value: 255 if value > 15 else 0).getbbox()
                assert content is None or (content[0] >= MULTI_CROP[0] and content[2] <= MULTI_CROP[2]), (filename, i, content)
                frame = frame.crop(MULTI_CROP)
            frame = frame.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            frames.append(frame)
            elapsed += original.info.get("duration", 100)
            ends.append(elapsed)
        if is_single:
            xy = ((index % 3) * 160, (index // 3) * 160)
        else:
            multi_index = index - 6
            xy = ((multi_index % 4) * 120, 320 + (multi_index // 4) * 120)
        animations.append({"file": str(path.relative_to(source)), "scene": scene, "agents": agents, "frames": frames, "ends": ends, "duration_ms": elapsed, "source_size": original.size, "tile_size": tile_size, "xy": xy, "mask": MASK if is_single else None, "crop": None if is_single else MULTI_CROP})
    return animations


def render(animations: list[dict], timestamp: int) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    for animation in animations:
        frame_index = bisect.bisect_right(animation["ends"], timestamp % animation["duration_ms"])
        canvas.paste(animation["frames"][min(frame_index, len(animation["frames"]) - 1)], animation["xy"])
    return canvas


def build_palette(animations: list[dict]) -> Image.Image:
    sheet = Image.new("RGB", (WIDTH * 5, HEIGHT), "white")
    for i, timestamp in enumerate((0, 2500, 4900, 7500, 9700)):
        sheet.paste(render(animations, timestamp), (WIDTH * i, 0))
    adaptive = sheet.quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    # Preserve the native robot/category colors even at small thumbnail scale.
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
    data = adaptive.getpalette()[:64 * 3] + [channel for color in semantic_colors for channel in color]
    data += [255] * (768 - len(data))
    palette = Image.new("P", (1, 1))
    palette.putpalette(data)
    return palette


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True, parents=True)
    animations = load_sources(args.source)
    duration = max(a["duration_ms"] for a in animations)
    timestamps = list(range(0, duration, 250))
    delays = [b - a for a, b in zip(timestamps, timestamps[1:] + [duration])]
    palette = build_palette(animations)
    frames = [render(animations, t).quantize(palette=palette, dither=Image.Dither.NONE) for t in timestamps]
    gif_path = args.output / "mdoc-thumbnail.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=delays, loop=0, disposal=1, optimize=True)

    encoded = Image.open(gif_path)
    assert encoded.n_frames == len(timestamps)
    actual_duration, decoded_samples = 0, []
    for i in range(encoded.n_frames):
        encoded.seek(i)
        actual_duration += encoded.info.get("duration", 0)
        if i in (0, 10, 20, 30, 40):
            decoded_samples.append(encoded.convert("RGB"))
    assert actual_duration == duration and encoded.info.get("loop") == 0
    for animation in animations:
        x, y = animation["xy"]
        size = animation["tile_size"]
        box = (x, y, x + size, y + size)
        assert any(ImageChops.difference(decoded_samples[0].crop(box), im.crop(box)).getbbox() for im in decoded_samples[1:]), animation["file"]
        if animation["mask"]:
            # Source annotations are fully white after masking and before resizing.
            for frame in animation["frames"]:
                region = frame.crop((0, 0, 35, 6))
                assert region.getextrema() == ((255, 255),) * 3, animation["file"]

    encoded.seek(10)
    encoded.convert("RGB").save(args.output / "mdoc-thumbnail-encoded-preview.png", optimize=True)
    encoded.seek(0)
    encoded.convert("RGB").save(args.output / "mdoc-thumbnail-first-frame.png", optimize=True)
    metadata = {
        "file": gif_path.name, "size": [WIDTH, HEIGHT], "frames": encoded.n_frames,
        "duration_ms": actual_duration, "fps": 4, "loop": "forever", "bytes": gif_path.stat().st_size,
        "layout": "Unlabeled white background; 6 single-robot environments in a 3×2 grid, followed by 8 multi-robot scenarios in a 4×2 grid.",
        "timing": "All clips start together. Original source playback speeds are retained; short clips loop independently within the 10.24 s composite loop.",
        "annotations": "No added text or borders. The diffusion counter in each single-robot source is masked white in source pixels (0, 0, 112, 24), after every source frame is checked against the known upper-left annotation footprint.",
        "checks": {"all_14_tiles_animate": True, "single_robot_text_region_masked": True, "multi_robot_crop_contains_all_geometry": True},
        "sources": [{k: v for k, v in a.items() if k not in ("frames", "ends")} | {"source_frames": len(a["frames"])} for a in animations],
    }
    (args.output / "mdoc-thumbnail-manifest.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: metadata[k] for k in ("file", "size", "frames", "duration_ms", "fps", "bytes", "checks")}, indent=2))


if __name__ == "__main__":
    main()
