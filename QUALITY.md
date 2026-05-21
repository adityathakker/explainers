# Explainer Quality Rulebook

This is the editorial standard for everything in this repo — `market/`, `insurance/`, and any future vertical. It overrides `market/STYLE-GUIDE.md` where they conflict. STYLE-GUIDE is *how* to author; this is *whether something is worth shipping*.

## The mission

Every article exists to prove **one specific thing the reader cannot prove by reading prose alone**.

If a static blog post can convey the idea, an interactive explainer is the wrong format. Pick topics where *the transformation is the point* — what happens when you change a parameter, how a system evolves, what a distribution looks like under different assumptions.

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

> *Prove this one thing: **\<X\>**. The reader will be able to **\<Y\>** when they finish. Build the widgets needed to land that. Stop when it's landed. The pilot at `market/options-insurance/` is your scope reference; `market/STYLE-GUIDE.md` is your component reference; this file is your editorial standard; everything else is your call.*

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
| H6 | Every `<a class="footnote-ref">` has a matching `<li id="fn-N">` in a `.footnotes` block |
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
| M1 | The *one-thing* the article proves is stated within the first 200 words |
| M2 | Every widget passes the *delete test* (removing it would weaken the argument) |
| M3 | The first screen surprises the reader — they don't already know the headline claim |
| M4 | Each widget teaches **one** concept, not three |
| M5 | Voice is present — there's a "you" being spoken to and an "I" doing the talking |
| M6 | Specificity over generality — concrete names, numbers, dates appear in every section |
| M7 | At least one *"well, actually 🧐"* sidenote admits where the simple model breaks |
| M8 | A non-expert friend can teach the one-thing back to you in two sentences |

When you ship an article, run the validator and visually confirm the manual-review items pass. Both are required for a green ship.
