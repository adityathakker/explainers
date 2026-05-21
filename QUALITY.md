# Explainer Quality Rulebook

This is the editorial standard for everything in this repo — `market/`, `insurance/`, and any future vertical. It overrides `shared/STYLE-GUIDE.md` where they conflict. STYLE-GUIDE is *how* to author; this is *whether something is worth shipping*.

## The mission

Every article exists to prove **one specific thing the reader cannot prove by reading prose alone**.

If a static blog post can convey the idea, an interactive explainer is the wrong format. Pick topics where *the transformation is the point* — what happens when you change a parameter, how a system evolves, what a distribution looks like under different assumptions.

## Two valid modes

Articles in this repo come in two flavors. Both are legitimate; the quality bar applies differently to each.

### Mode A — Single-claim explainer

Proves one specific, surprising claim. Example: *"Your 12.5% Nifty return is near-zero in real terms"* (`real-returns`); *"Every return decomposes into PE × EPS, and one of those numbers is usually lying"* (`what-moves-prices`); *"Options are insurance, not gambling"* (`options-insurance`).

The one-thing is **a claim**. The widgets prove it. A non-expert leaves repeating the claim.

### Mode B — Framework / playbook

Teaches a structured method or decision framework rather than a single claim. Example: *the 4-tier consumer framework* (`india-consumption`); *the 6-point business investability scorer* (`evaluating-businesses`); *the position-sizing rules with Kelly + ruin + cliff* (`position-sizing`); *the sell-discipline 5-rule playbook* (`sell-discipline`).

The one-thing is **the framework itself**. The widgets demonstrate each dimension. A non-expert leaves able to name the framework and its dimensions.

Mode is determined by the article, not declared. The validator and reviewer should infer it from the structure and apply the right rubric.

How M1, M3, M8 differ by mode:

| Rule | Mode A (single claim) | Mode B (framework) |
|---|---|---|
| **M1** — stated in first 200 words | The surprising claim must appear early | The framework's name and purpose must appear early |
| **M3** — first screen surprises | The headline claim should be counter-intuitive | The framework's existence or novelty should be the hook |
| **M8** — teachable in 2 sentences | "A puts cap your loss at premium + (S₀−K). That's the entire thing." | "The 4-tier framework segments by discretionary spend capacity: ₹>15L (luxury), ₹5-15L (middle), ₹<5L (lower), survival. That's the entire thing." |

M2, M4, M5, M6, M7 apply identically in both modes.

## Before writing a word

The author writes two sentences in a notebook:

1. **The thing I am proving:** *e.g. "A 10% loss requires a 22% gain to break even — not 10%."*
2. **The widget that proves it:** *e.g. "A draggable utility curve with a fixed reference line at 0."*

If you can't fill both sentences in 60 seconds, you don't understand the topic well enough yet.

## Quality principles (non-negotiable)

1. **Surprise per scroll.** Every screenful either tells the reader something they didn't know or contradicts something they thought they knew. No screen exists just to recap.
2. **Interactivity must reveal, not decorate.** Every widget passes the *delete test*: if removing it would not weaken the argument, it shouldn't be there. A widget that confirms what the prose just said is a failure.
3. **Specificity over generality.** "Meta's $100B 2026 capex" beats "tech companies spend on AI." Names, numbers, dates make the abstract real.
4. **One concept per widget.** A widget that teaches three things teaches none. If you need three concepts, build three widgets.
5. **The first 200 words must hook.** State the surprising thing immediately. Don't ease in. Don't define terms first.
6. **Voice is required.** It's not Wikipedia. There's a "you" being spoken to and an "I" doing the talking. The author has an opinion and shows it.
7. **Math when it clarifies, never when it intimidates.** A formula appears when seeing it makes the prose shorter, not when it makes the author look serious.
8. **Admit where the simple model breaks.** The "Well, actually 🧐" sidenote that flags a regime break earns more trust than ten paragraphs of polish. Honesty is a quality signal.
9. **The reader leaves able to do something.** After reading, they can predict an outcome, explain it to a friend, or debug their intuition.

## Friction rules (experience layer)

- **Sliders update live.** Never "click to apply."
- **Buttons look like buttons.** No hidden affordances.
- **No login, consent popup, email-capture modal, or analytics overlay.** Friction kills curiosity faster than bad writing.
- **Works on a 4-year-old phone.** Static HTML, zero dependencies, no build step.
- **Loads in under a second on 4G.** Single file, inline CSS/JS, fonts deferred.
- **Scroll is the only navigation that matters.** TOCs are optional. Search is optional. The article reads top-to-bottom by default.

## What is explicitly NOT a quality bar

- **Line count.** Replaced by "until the one-thing is proven, then stop."
- **Mandatory section count.** Some topics need 5 sections, some need 12. Don't force-fit.
- **Required widget count.** A 2-widget article that lands beats a 6-widget article that meanders.
- **Section numbering ceremony.** Use Roman numerals when they add structure; drop them when they add ceremony.

## The single quality test

Before publishing, give a smart friend who isn't an expert in the topic the article. Watch them read it. Two failure modes to listen for:

- **"Wait, I missed something — let me go back."** → Pacing too dense. Cut.
- **"OK, got it, what's next."** → No surprise on that screen. Earn the surprise or delete the screen.

Ship when the friend can teach the *one-thing* back to you in two sentences without re-reading.

## The brief, if you must have one

For agents or collaborators writing a new article, the entire brief should be:

> *Prove this one thing: **\<X\>**. The reader will be able to **\<Y\>** when they finish. Build the widgets needed to land that. Stop when it's landed. The pilot at `market/options-insurance/` is your scope reference; `shared/STYLE-GUIDE.md` is your component reference; this file is your editorial standard; everything else is your call.*

That's it. No line counts. No widget counts. No mandatory sections.

## Validation checklist

Mechanically-checkable rules run by `validate-explainers.py` at the repo root. Run it before every commit that touches an article:

```bash
python3 validate-explainers.py
```

### Hard checks (must pass)

| # | Rule |
|---|---|
| H1 | HTML parses without errors |
| H2 | All inline `<script>` blocks are valid JavaScript |
| H3 | No external JS libraries (only Google Fonts CSS allowed) |
| H4 | `setupHiDPICanvas` is never called with an explicit `width` |
| H5 | Hero meta does not contain "Synthesized from 0 posts" |
| H6 | Every inline `<a class="footnote-ref">` resolves to a matching `<li id="fn-N">` target (broken anchors fail). An `<ol class="footnotes">` block with reference-only entries (no inline anchors) is permitted — that's a "References" section, valid for engineering-style articles. |
| H7 | Every `<canvas>` widget is followed by a `.widget-hint` within the same `.demo` container |

### Soft checks (warnings only)

| # | Rule |
|---|---|
| S1 | Article has at least one `<canvas>` widget OR is explicitly tagged as prose-heavy |
| S2 | Article has at least one `<details class="sidenote">` |
| S3 | Article has at least one `.footnote-ref` |
| S4 | Article has at least one `.math-block` (relaxed — not required) |
| S5 | Hero `--accent` is set in an inline `<style>` block |
| S6 | At least 60% of section headings end with a question mark (the "question-driven" signal) |
| S7 | Article links to its parent vertical's landing via `.nav__back` |

### Manual review (not automated — author/reviewer judgment)

| # | Rule |
|---|---|
| M1 | The *one-thing* (Mode A: the claim; Mode B: the framework's name + purpose) is stated within the first 200 words |
| M2 | Every widget passes the *delete test* (removing it would weaken the argument) |
| M3 | The first screen surprises the reader — they don't already know the headline (Mode A: claim; Mode B: framework existence/novelty) |
| M4 | Each widget teaches **one** concept, not three |
| M5 | Voice is present — there's a "you" being spoken to and an "I" doing the talking |
| M6 | Specificity over generality — concrete names, numbers, dates appear in every section |
| M7 | At least one *"well, actually 🧐"* sidenote admits where the simple model breaks |
| M8 | A non-expert friend can teach the one-thing back (Mode A: claim in 2 sentences; Mode B: framework name + dimensions in 2 sentences) |

When you ship an article, run the validator and visually confirm the manual-review items pass. Both are required for a green ship.
