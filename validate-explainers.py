#!/usr/bin/env python3
"""
validate-explainers.py — Mechanical quality check for every article in this
repo, against the rules in QUALITY.md.

Usage:
    python3 validate-explainers.py            # check all
    python3 validate-explainers.py market/foo # check one article folder
    python3 validate-explainers.py --json     # machine-readable output

Exit code: 0 if all hard checks pass on every article, 1 if any fail.
"""
from __future__ import annotations
import html.parser
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent
VERTICALS = ["market", "insurance", "starlink", "monetary"]
# Files we skip (verticals' own landing pages, not articles)
SKIP_RELATIVE = {"market/index.html", "insurance/index.html", "starlink/index.html", "monetary/index.html"}

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class Check:
    code: str           # H1, S2, etc.
    name: str
    status: str         # "pass", "fail", "warn", "skip"
    detail: str = ""

@dataclass
class ArticleReport:
    path: str
    hard: List[Check] = field(default_factory=list)
    soft: List[Check] = field(default_factory=list)
    info: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(c.status == "pass" for c in self.hard)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_articles() -> List[Path]:
    out: List[Path] = []
    for vert in VERTICALS:
        vroot = REPO_ROOT / vert
        if not vroot.is_dir(): continue
        for child in sorted(vroot.iterdir()):
            if not child.is_dir(): continue
            idx = child / "index.html"
            if not idx.is_file(): continue
            rel = idx.relative_to(REPO_ROOT).as_posix()
            if rel in SKIP_RELATIVE: continue
            out.append(idx)
    return out


class HTMLValidator(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors: List[str] = []
    def error(self, msg: str) -> None:
        self.errors.append(msg)


def parse_html(src: str) -> List[str]:
    v = HTMLValidator()
    v.feed(src)
    return v.errors


def parse_inline_scripts(src: str) -> tuple[int, List[str]]:
    """Returns (count, errors). Uses Node's Function constructor to syntax-check
    each inline <script>. Writes to a temp file so quoting is bulletproof."""
    import tempfile
    pat = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>', re.I)
    scripts = pat.findall(src)
    if not scripts:
        return 0, []
    errors: List[str] = []
    for i, body in enumerate(scripts, 1):
        # Wrap body in `new Function()` so top-level returns/awaits don't trip
        # the parser; if the syntax is invalid, the SyntaxError surfaces.
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write("try { new Function(" + json.dumps(body) + "); } catch (e) { console.error(e.message); process.exit(1); }")
            tmp_path = f.name
        try:
            subprocess.run(
                ["node", tmp_path],
                capture_output=True, text=True, timeout=20, check=True,
            )
        except subprocess.CalledProcessError as e:
            err_line = (e.stderr or "").strip().splitlines()
            errors.append(f"script #{i}: {err_line[-1] if err_line else 'parse error'}")
        except FileNotFoundError:
            errors.append("node not available — install Node.js to run JS-parse check")
            os.unlink(tmp_path)
            break
        finally:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
    return len(scripts), errors


def find_external_scripts(src: str) -> List[str]:
    """Return external <script src=...> URLs (excluding repo-relative paths and Google Fonts)."""
    pat = re.compile(r'<script[^>]*\bsrc=["\']([^"\']+)["\']', re.I)
    bad = []
    for url in pat.findall(src):
        if url.startswith("http://") or url.startswith("https://"):
            if "fonts.googleapis" in url or "fonts.gstatic" in url:
                continue
            bad.append(url)
    return bad


# ---------------------------------------------------------------------------
# Per-rule checks
# ---------------------------------------------------------------------------

def check_article(path: Path) -> ArticleReport:
    rel = path.relative_to(REPO_ROOT).as_posix()
    rep = ArticleReport(path=rel)
    src = path.read_text(encoding="utf-8", errors="replace")
    line_count = src.count("\n") + 1
    rep.info["lines"] = line_count

    # ---------- HARD CHECKS ----------
    # H1 HTML parses
    errs = parse_html(src)
    rep.hard.append(Check("H1", "HTML parses",
        "pass" if not errs else "fail",
        "; ".join(errs[:3]) if errs else ""))

    # H2 inline scripts parse
    n, errs = parse_inline_scripts(src)
    rep.info["inline_scripts"] = n
    if errs and errs[0].startswith("node not available"):
        rep.hard.append(Check("H2", "Inline scripts parse", "skip", errs[0]))
    else:
        rep.hard.append(Check("H2", "Inline scripts parse",
            "pass" if not errs else "fail",
            "; ".join(errs[:2]) if errs else f"{n} scripts"))

    # H3 no external JS libs
    ext = find_external_scripts(src)
    rep.hard.append(Check("H3", "No external JS libs",
        "pass" if not ext else "fail",
        "; ".join(ext) if ext else ""))

    # H4 setupHiDPICanvas with width
    bad_width = re.findall(r"setupHiDPICanvas\s*\([^)]*\bwidth\s*:", src)
    rep.hard.append(Check("H4", "No hardcoded canvas width",
        "pass" if not bad_width else "fail",
        f"{len(bad_width)} occurrence(s)" if bad_width else ""))

    # H5 no "Synthesized from 0 posts"
    bad_meta = "Synthesized from 0 posts" in src
    rep.hard.append(Check("H5", "Hero meta is real",
        "fail" if bad_meta else "pass",
        '"Synthesized from 0 posts" found' if bad_meta else ""))

    # H6: inline footnote refs must resolve to matching targets (broken links = FAIL).
    # Orphan targets (References section without inline anchors) are valid for
    # academic/engineering articles; pass with detail note, not hard fail.
    refs = set(re.findall(r'<a[^>]*class="footnote-ref"[^>]*href="#fn-([^"]+)"', src))
    targets = set(re.findall(r'<li[^>]*id="fn-([^"]+)"', src))
    orphan_refs = refs - targets
    orphan_targets = targets - refs
    if not refs and not targets:
        rep.hard.append(Check("H6", "Footnote refs match targets", "pass", "no footnotes"))
    elif orphan_refs:
        rep.hard.append(Check("H6", "Footnote refs match targets", "fail",
                              f"refs without targets: {sorted(orphan_refs)}"))
    else:
        detail = f"{len(refs)} pair(s)"
        if orphan_targets:
            detail += f"; {len(orphan_targets)} reference-only entries (no inline anchor)"
        rep.hard.append(Check("H6", "Footnote refs match targets", "pass", detail))

    # H7 every canvas widget has a .widget-hint within the same .demo container
    # Match each .demo block, check for canvas + widget-hint inside.
    demos = re.findall(r'<div class="demo[^"]*"[^>]*>([\s\S]*?)</div>\s*(?:<p class="widget-hint"|<div|<section|<details|<hr|</div>)', src)
    canvas_in_demo = [d for d in demos if "<canvas" in d]
    # Simpler approach: split src into "demo" + "next sibling" pairs
    bad_demos = []
    for m in re.finditer(r'<div class="demo[^"]*"[^>]*>([\s\S]*?</div>)\s*((?:<[^>]+>\s*){0,3})', src):
        demo_body = m.group(1)
        following = m.group(2)
        if "<canvas" in demo_body:
            # The widget-hint can be INSIDE the demo (before its closing </div>) OR immediately after
            inside_hint = 'class="widget-hint"' in demo_body
            following_hint = 'class="widget-hint"' in following
            if not (inside_hint or following_hint):
                bad_demos.append(demo_body[:80].replace("\n", " "))
    rep.hard.append(Check("H7", "Each canvas widget has a widget-hint",
        "pass" if not bad_demos else "fail",
        f"{len(bad_demos)} widget(s) missing hint" if bad_demos else ""))

    # ---------- SOFT CHECKS ----------
    # S1 has a canvas
    n_canvas = src.count("<canvas")
    rep.info["canvases"] = n_canvas
    rep.soft.append(Check("S1", "Has at least one canvas widget",
        "pass" if n_canvas >= 1 else "warn",
        f"{n_canvas} canvas(es)"))

    # S2 has at least one sidenote
    n_sidenote = src.count('class="sidenote"')
    rep.info["sidenotes"] = n_sidenote
    rep.soft.append(Check("S2", "Has at least one sidenote",
        "pass" if n_sidenote >= 1 else "warn",
        f"{n_sidenote} sidenote(s)"))

    # S3 has at least one footnote-ref
    n_fnref = len(refs)
    rep.info["footnotes"] = n_fnref
    rep.soft.append(Check("S3", "Has at least one footnote",
        "pass" if n_fnref >= 1 else "warn",
        f"{n_fnref} footnote(s)"))

    # S4 has at least one math-block
    n_math = src.count('class="math-block"')
    rep.info["math_blocks"] = n_math
    rep.soft.append(Check("S4", "Has at least one math-block",
        "pass" if n_math >= 1 else "warn",
        f"{n_math} math-block(s)"))

    # S5 has inline --accent override
    has_accent = bool(re.search(r"<style>[\s\S]*?--accent\s*:", src))
    rep.soft.append(Check("S5", "Inline --accent override",
        "pass" if has_accent else "warn",
        "set" if has_accent else "missing"))

    # S6 question-driven section headings (≥50% end with ?). The pilot has 5/9,
    # so a half-and-half mix is the floor, not the target.
    h2s = re.findall(r'<h2[^>]*>([^<]+)</h2>', src)
    if h2s:
        questions = sum(1 for h in h2s if h.strip().rstrip('.').endswith("?"))
        ratio = questions / len(h2s)
        rep.info["h2_count"] = len(h2s)
        rep.info["h2_questions"] = questions
        rep.soft.append(Check("S6", "Question-driven headings",
            "pass" if ratio >= 0.5 else "warn",
            f"{questions}/{len(h2s)} end with '?'"))
    else:
        rep.soft.append(Check("S6", "Question-driven headings", "warn", "no h2 found"))

    # S7 has .nav__back
    has_back = 'class="nav__back"' in src or 'class="nav-back"' in src
    rep.soft.append(Check("S7", "Has back-nav to vertical landing",
        "pass" if has_back else "warn",
        "" if has_back else "missing"))

    return rep


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

ICON = {"pass": "✓", "fail": "✗", "warn": "!", "skip": "—"}


def print_text_report(reports: List[ArticleReport]) -> int:
    total_articles = len(reports)
    total_hard_fails = sum(1 for r in reports for c in r.hard if c.status == "fail")
    total_warns = sum(1 for r in reports for c in r.soft if c.status == "warn")

    # Per-article block
    for r in reports:
        status_icon = "✓" if r.passed else "✗"
        print(f"\n{status_icon} {r.path}   ({r.info.get('lines', 0)} lines, "
              f"{r.info.get('canvases', 0)} widgets, "
              f"{r.info.get('sidenotes', 0)} sidenotes, "
              f"{r.info.get('footnotes', 0)} footnotes)")
        for c in r.hard:
            if c.status != "pass":
                print(f"  {ICON[c.status]} [{c.code}] {c.name}  {c.detail}")
        warns = [c for c in r.soft if c.status == "warn"]
        for c in warns:
            print(f"  {ICON[c.status]} [{c.code}] {c.name}  {c.detail}")
        if r.passed and not warns:
            print(f"  ✓ all checks pass")

    # Summary
    print("\n" + "=" * 64)
    print(f"  Articles checked: {total_articles}")
    print(f"  Hard failures:    {total_hard_fails}")
    print(f"  Warnings:         {total_warns}")
    print("=" * 64)
    if total_hard_fails == 0:
        print("\nAll hard checks pass. Run the manual-review checklist (M1-M8 in QUALITY.md) before declaring an article shipped.\n")
    else:
        print("\nFix hard failures before shipping. Warnings are informational; address those where they apply.\n")
    return 1 if total_hard_fails > 0 else 0


def print_json_report(reports: List[ArticleReport]) -> int:
    payload = {
        "articles": [
            {
                "path": r.path,
                "info": r.info,
                "passed": r.passed,
                "hard": [c.__dict__ for c in r.hard],
                "soft": [c.__dict__ for c in r.soft],
            }
            for r in reports
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0 if all(r.passed for r in reports) else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    json_mode = "--json" in argv
    targets_arg = [a for a in argv[1:] if not a.startswith("--")]
    articles = find_articles()
    if targets_arg:
        wanted = set(targets_arg)
        articles = [a for a in articles
                    if a.parent.name in wanted or a.relative_to(REPO_ROOT).as_posix().startswith(tuple(wanted))]
    if not articles:
        print("No articles found.", file=sys.stderr)
        return 1
    reports = [check_article(a) for a in articles]
    if json_mode:
        return print_json_report(reports)
    return print_text_report(reports)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
