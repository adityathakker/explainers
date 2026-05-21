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

For articles outside `market/` (e.g. `insurance/<topic>/`), link to `../../shared/explainer.css` and helpers.

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
  <link rel="stylesheet" href="../../shared/explainer.css">
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
<script src="../../shared/chart-canvas-helpers.js"></script>
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

## Polish gotchas (learned the hard way)

These are real bugs we shipped and fixed. Treat them as forced checks before declaring an article done.

### 1. Never pass an explicit `width` to `setupHiDPICanvas`

```js
// ✗ WRONG — hardcodes 600px, overflows the .demo container on narrow viewports
setupHiDPICanvas(canvas, { width: 600, height: 320 });

// ✓ RIGHT — auto-detects from canvas's rendered width (style="width: 100%")
setupHiDPICanvas(canvas, { height: 320 });
```

The helper reads `getBoundingClientRect().width` when `width` is omitted. The canvas's `style="width: 100%"` then makes it perfectly fit its `.demo` parent, regardless of viewport size.

### 2. Position widget labels so they can't collide

Two specific traps:
- **Strike-line label vs chart title.** If both sit near the top of the canvas at horizontal centre, they overlap when the strike happens to land near centre. Put the strike label at the *bottom* of its dashed line (hugging the x-axis), and put the title at `y = 10` (above the plot area). They occupy different y-bands by construction.
- **Plot title vs data points.** If a data point's y-coordinate can reach the top of the plot, the title above can collide. Either reserve extra top-padding (`pad.top = 28+`) or put the title above the canvas entirely (negative y) — never overlapping.

### 3. The hero gradient now derives from `--accent` by default

You no longer need a per-article `.hero { background: linear-gradient(...) }` override. Setting `--accent` in the inline `<style>` block is enough — the shared CSS builds a two-tone gradient from accent → lighter mix-with-white. Only override the hero background if you want a specific non-derived pair.

### 4. The article hero meta uses real numbers, not template fill

```html
✗ <p class="hero__meta">Synthesized from 0 posts &middot; 22 min read</p>
✓ <p class="hero__meta">22 min read</p>
✓ <p class="hero__meta">9 chapters &middot; 6 simulations &middot; 30 min read</p>
```

No "Synthesized from 0 posts" anywhere. If you want a count, use a real one.

### 5. The landing page card needs a description + meta, not an empty body

Every new article added to `market/index.html` needs both:

```html
<a href="my-topic/index.html" class="card">
  <div class="card-hero" style="background: linear-gradient(135deg, #1a365d 0%, #2b6cb0 100%);">
    <h2>My Article Title</h2>
    <span class="card-badge">Updated</span>  <!-- optional -->
  </div>
  <div class="card-body">
    <p>One-line description — same text as the article's hero__subtitle works well.</p>
    <div class="card-meta">22 min read</div>
  </div>
</a>
```

The `card-badge` is a glassy "Updated" pill in the top-right of the hero — use it to mark articles that have been refreshed to the new style.

### 6. Insurance and other verticals belong on the landing too

`market/index.html` has two `<section class="section">` groups: "Markets & Investing" (18 cards) and "Insurance" (1 card linking up to `../insurance/actuarial-pricing/`). Don't orphan articles in sibling directories — link them from the main landing under their own section label.

### 7. Run the parse smoke-test before declaring done

Before claiming an article rewrite is complete:

```bash
# HTML parses without errors
python3 -c "import html.parser; p=html.parser.HTMLParser(); open('market/X/index.html').read()" \
  | python3 -c "import sys,html.parser; p=html.parser.HTMLParser(); p.feed(sys.stdin.read())"

# All inline scripts parse as JS
node -e "
const html = require('fs').readFileSync('market/X/index.html', 'utf-8');
const re = /<script(?![^>]*src)[^>]*>([\s\S]*?)<\/script>/g;
let m, errors = [];
while ((m = re.exec(html)) !== null) try { new Function(m[1]); } catch(e) { errors.push(e.message); }
console.log(errors.length ? errors : 'OK');
"

# Server returns 200
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/market/X/
```

Three checks, ~3 seconds total. Catches 90% of mechanical breakage before the user does.
