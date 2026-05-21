# Explainer Style Guide

Working reference for authoring new market/insurance explainers in this repo. Keep this file open while writing.

## File layout

```
market/
  explainer.css            ← shared styles. Don't duplicate inline.
  chart-helpers.js         ← SVG drawing primitives (static charts)
  chart-canvas-helpers.js  ← Canvas + animation (interactive sims)
  <topic>/
    index.html             ← one file per article
```

For articles outside `market/` (e.g. `insurance/<topic>/`), link to `../../market/explainer.css` and helpers.

## Required `<head>` boilerplate

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Article Title — Market Explainers</title>
  <meta name="description" content="One-line hook">
  <meta property="og:title" content="Article Title">
  <meta property="og:description" content="Same hook">
  <meta property="og:type" content="article">
  <link rel="icon" href="../favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,700;1,6..72,400&family=Figtree:wght@400;600&family=Source+Code+Pro:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../explainer.css">
  <style>
    :root {
      --accent: #1a365d;
      --accent-light: color-mix(in srgb, var(--accent) 10%, #FAF9F7);
    }
  </style>
</head>
```

## Page structure

```
<body>
  <nav class="nav">         ← back link to index
  <header class="hero">     ← title, subtitle, meta
  <div class="container">
    <div class="toc-wrapper reveal">  ← table of contents
  <article class="article">
    <section class="reveal" id="...">    ← one per chapter
      <div class="section-heading">
        <div class="section-number">I.</div>   ← manual Roman numeral
        <h2>I. Section title</h2>
      </div>
      <div class="section-content">
        ...prose, widgets, sidenotes, footnote refs...
      </div>
    </section>
    <ol class="footnotes">  ← end of article, before </article>
  </article>
  <footer class="footer">
  <script>...reveal observer, smooth scroll, widget code...</script>
</body>
```

## Components

### Prose

- Paragraphs: just `<p>`. Body is Newsreader serif at 18.5px.
- Lead with the strongest sentence. Don't bury the headline.
- One idea per paragraph. Long paragraphs lose readers.
- Use `<strong>` for the key claim, `<em>` for terms you're naming.

### Question-driven section headings

Prefer questions over noun phrases. `"Why doesn't 60/40 work anymore?"` beats `"Portfolio Construction Issues"`.

### Sidenote — "Well, actually 🧐"

For technical nuance the main prose deliberately skips. Collapsed by default.

```html
<details class="sidenote">
  <summary>Well, actually 🧐 — short hook</summary>
  <p>The detail the prose skipped.</p>
</details>
```

When to use: technical precision, derivations, exceptions, contrarian takes that would derail the main thread.

### Footnotes

For source citations and bibliographic detail. Numbered, with back-anchors.

Inline:
```html
LTCG was 0% before 2018<a class="footnote-ref" id="fnref-1" href="#fn-1">[1]</a>.
```

End of article (just before `</article>`):
```html
<ol class="footnotes">
  <li id="fn-1">Full citation or source detail. <a class="footnote-back" href="#fnref-1">&#8617;</a></li>
</ol>
```

When to use: external references, dates, sources. Not for "fun extras" — that's a sidenote.

### Math

```html
Inline: the <span class="math">σ² of returns</span> matters more than μ.

Block:
<div class="math-block">
  r<sub>real</sub> = (1 + r<sub>nom</sub>) ÷ (1 + π) − 1
  <span class="math-where">where π is realised inflation</span>
</div>
```

Don't pull in MathJax/KaTeX. Use Unicode (σ, μ, π, ≈, ÷, ×, −, ≤, ≥, ∑, ∫) plus `<sub>` / `<sup>`. Reads fine, ships zero bytes.

### Callout

Big, opinionated takeaway. Use sparingly — once or twice per article.

```html
<div class="callout">
  <div class="callout-title">The point</div>
  <p>Your competition is not other investors. It is inflation.</p>
</div>
```

### Demo / interactive widget

The `.demo` container holds canvas/SVG sims. Pair every widget with a `.widget-hint` underneath telling the reader what to do.

```html
<div class="demo reveal" id="widget-1">
  <div class="demo-title">Drag the strike</div>
  <canvas id="canvas-1" style="width: 100%; height: 320px;"></canvas>
  <div class="slider-group">
    <div class="slider-label"><span>Strike</span><span class="slider-value" id="strike-val">100</span></div>
    <input type="range" id="strike" min="50" max="150" value="100" step="1">
  </div>
</div>
<p class="widget-hint">Drag to see how the payoff hockey-stick shifts.</p>
```

### Stats row, callout, data-table

`stat-row` / `stat` / `stat-value` / `stat-label` for at-a-glance numbers. `.data-table` for tabular data. See `explainer.css` for class details.

## Canvas widget skeleton

```html
<script src="../chart-canvas-helpers.js"></script>
<script>
(function() {
  const canvas = document.getElementById('canvas-1');
  if (!canvas) return;
  const { ctx, w, h } = setupHiDPICanvas(canvas, { width: 600, height: 320 });

  function draw(state) {
    clearCanvasCtx(ctx, w, h, '#FAF9F7');
    drawAxesCanvas(ctx, w, h, { yMin: -50, yMax: 50, xLabels: ['80','100','120'] });
    // ...your drawing code, using mapX/mapY...
  }

  const getValues = attachSliders([
    { el: document.getElementById('strike'),
      label: document.getElementById('strike-val'),
      format: v => v.toFixed(0) }
  ], draw);
})();
</script>
```

For animated widgets, wrap the draw call in `animate(fn)` and call `.start()` on a play button click.

## Accent color palette

Existing gradient pairs used by articles — keep variety across the index page.

| Theme         | --accent  | Gradient pair         |
|---------------|-----------|-----------------------|
| Deep blue     | `#1a365d` | `#1a365d → #2b6cb0`   |
| Purple        | `#44337a` | `#44337a → #805ad5`   |
| Dark slate    | `#1a202c` | `#1a202c → #4a5568`   |
| Crimson       | `#63171b` | `#63171b → #c53030`   |
| Teal          | `#285e61` | `#285e61 → #319795`   |
| Forest        | `#22543d` | `#22543d → #38a169`   |
| Charcoal      | `#2d3748` | `#2d3748 → #718096`   |

The hero gradient is hardcoded in each article's `<header class="hero" style="background: ...">` — `--accent` is set in the `<style>` block.

## Writing checklist

Before shipping a new article:

1. **Hero subtitle** is one sentence, not two
2. **TOC** has 7-11 sections, each numbered I, II, III...
3. **Every section** ends with either a widget, a callout, or a clear paragraph (not a dangling list)
4. **At least one** `<details class="sidenote">` — there's almost always a nuance worth flagging
5. **All numeric claims** that need sourcing have a `<a class="footnote-ref">` → matching `<li id="fn-X">`
6. **Widgets** all have `.widget-hint` underneath
7. **Reveal animations** work — every top-level section has `class="reveal"`
8. **Per-page accent** is set and matches the landing-page card gradient
9. **Mobile** check at 480px — sidenotes, footnotes, math-blocks should all reflow without horizontal scroll

## When in doubt

Open `real-returns/index.html` and copy the pattern. It's the canonical reference for sidenote + footnote + math-block + widget-hint usage. The full pilot reference lives in `options-insurance/index.html` (gold standard for canvas widgets).
