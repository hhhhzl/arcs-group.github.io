---
layout: publication
title: "Model-Based Diffusion Optimal Control for Multi-Robot Motion Planning"
permalink: /publications/HeRSS26/
full-width: true
share-description: "MDOC combines model-based diffusion, control barrier function constraints, and conflict-based search for dynamically feasible multi-robot motion planning without demonstration data."
share-img: /files/zhilinhe/mdoc-thumbnail.jpg
css:
  - /assets/css/mdoc.css
---
{% assign pub_key = "HeRSS26" %}
{% include base_path %}
{% assign pub = site.data.pubs | where: "key", pub_key | first %}

<article class="mdoc-project">
  <header class="mdoc-header">
    <p class="mdoc-eyebrow">Robotics: Science and Systems · 2026</p>
    <h1>{{ pub.title }}</h1>
    <p class="mdoc-authors">{{ pub.authors | join: ", " }}</p>
    <nav class="mdoc-resources" aria-label="Paper resources">
      {% include pub-buttons.html %}
    </nav>
    <p class="mdoc-intro">From single-robot trajectory optimization to multi-robot coordination: planning with known dynamics, without demonstration data.</p>
  </header>

  <figure class="mdoc-overview">
    <a href="{{ '/files/zhilinhe/mdoc-overview.gif' | relative_url }}" aria-label="Open all MDOC demonstrations at full size">
      <img src="{{ '/files/zhilinhe/mdoc-overview.gif' | relative_url }}" alt="Animated overview of all six single-robot MDOC environments and eight multi-robot MDOC-CBS scenarios." width="1200" height="1584" decoding="async">
    </a>
    <figcaption>Six single-robot environments with MDOC, and eight multi-robot scenarios with MDOC-CBS. Each panel loops at its original playback speed. <a href="{{ '/files/zhilinhe/mdoc-overview.gif' | relative_url }}">Open full size</a> · <a href="{{ '/files/zhilinhe/mdoc-overview.gif' | relative_url }}" download>Download GIF</a></figcaption>
  </figure>

  <section class="mdoc-section" aria-labelledby="mdoc-method">
    <h2 id="mdoc-method">How it works</h2>
    <div class="mdoc-method-grid">
      <div>
        <span class="mdoc-step">01</span>
        <h3>Model-based diffusion</h3>
        <p>Optimize trajectories using known dynamics, without training on a demonstration dataset.</p>
      </div>
      <div>
        <span class="mdoc-step">02</span>
        <h3>Constrained planning</h3>
        <p>Combine dynamics models with Control Barrier Function-constrained projections to enforce trajectory constraints.</p>
      </div>
      <div>
        <span class="mdoc-step">03</span>
        <h3>Multi-robot coordination</h3>
        <p>Integrate MDOC with Conflict-Based Search to resolve collisions between robots.</p>
      </div>
    </div>
  </section>

  <section class="mdoc-section mdoc-abstract" aria-labelledby="mdoc-abstract">
    <h2 id="mdoc-abstract">Abstract</h2>
    {{ pub.abstract | markdownify }}
  </section>

  <section class="mdoc-section" aria-labelledby="mdoc-citation">
    <h2 id="mdoc-citation">Citation</h2>
    <pre class="mdoc-citation"><code>{{ pub.bib | escape }}</code></pre>
  </section>
</article>
