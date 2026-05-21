#!/usr/bin/env python3
"""
validate-quality-agent.py — LLM-based subjective quality check against QUALITY.md.

Counterpart to validate-explainers.py:
  validate-explainers.py    runs the H1-H7 / S1-S7 mechanical checks.
  validate-quality-agent.py runs the M1-M8 manual-review checks via Claude,
                            which require reading and judgment.

Uses the `claude` CLI in print mode (no API key needed; uses your Claude
Code auth). Each article goes to the model with QUALITY.md as context and
returns a structured per-rule verdict.

Usage:
    python3 validate-quality-agent.py                          # all articles
    python3 validate-quality-agent.py market/options-insurance # one article
    python3 validate-quality-agent.py --json                   # JSON output
    python3 validate-quality-agent.py --model opus             # use Opus
    python3 validate-quality-agent.py --parallel 4             # 4 concurrent
    python3 validate-quality-agent.py --cache                  # skip articles already in .quality-cache.json

Exit code: 0 if every M-rule passes or warns. 1 if any rule fails on any article.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent
QUALITY_MD = REPO_ROOT / "QUALITY.md"
CACHE_FILE = REPO_ROOT / ".quality-cache.json"
VERTICALS = ["market", "insurance"]
SKIP_RELATIVE = {"market/index.html", "insurance/index.html"}

DEFAULT_MODEL = "sonnet"
DEFAULT_PARALLELISM = 3

M_RULES = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8"]

PROMPT_TEMPLATE = """You are evaluating an interactive explainer article against the manual-review rules M1-M8 in QUALITY.md. The full editorial standard is below.

<quality-md>
{quality_md}
</quality-md>

<article path="{article_path}">
{article_html}
</article>

For each rule M1 through M8, return a verdict object:
  - "status": "pass" | "warn" | "fail"
  - "evidence": a SHORT (1-2 sentence) quote, paraphrase, or specific reference to what supports the verdict
  - "suggestion": a SHORT (1-2 sentence) concrete change to fix it (omit this field if status is "pass")

Then add an "overall" field with a 2-3 sentence summary of the article's quality.

Return ONLY valid JSON, with NO surrounding prose or code fences, in exactly this shape:

{{
  "M1": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M2": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M3": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M4": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M5": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M6": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M7": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "M8": {{"status": "...", "evidence": "...", "suggestion": "..."}},
  "overall": "..."
}}

Be strict but specific. Honest is more useful than kind. Quote actual phrases from the article when you can — vague evidence is a failure of the review, not the article."""


@dataclass
class Verdict:
    rule: str
    status: str
    evidence: str = ""
    suggestion: str = ""


@dataclass
class Report:
    path: str
    verdicts: List[Verdict] = field(default_factory=list)
    overall: str = ""
    error: Optional[str] = None
    seconds: float = 0.0

    @property
    def has_fail(self) -> bool:
        return any(v.status == "fail" for v in self.verdicts) or self.error is not None


# ---------------------------------------------------------------------------
# Article discovery
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


# ---------------------------------------------------------------------------
# Claude CLI call
# ---------------------------------------------------------------------------

def strip_scripts(html: str) -> str:
    """Remove inline <script> blocks. We're evaluating prose and structure,
    not JS. Cuts token cost ~50%."""
    return re.sub(r'<script[\s\S]*?</script>', '<!-- script omitted -->', html, flags=re.I)


def extract_json(text: str) -> dict:
    """Pull a JSON object out of model output, tolerating code fences or
    leading explanation lines."""
    s = text.strip()
    # Strip ```json fences
    if s.startswith("```"):
        s = re.sub(r'^```(?:json)?\s*\n', '', s)
        s = re.sub(r'\n```\s*$', '', s)
    # Find the outermost {...}
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object found in model output (first 200 chars: {text[:200]!r})")
    return json.loads(s[start:end + 1])


def evaluate(article_path: Path, quality_md: str, model: str = DEFAULT_MODEL,
             timeout: int = 240) -> Report:
    rel = article_path.relative_to(REPO_ROOT).as_posix()
    rep = Report(path=rel)
    started = time.time()
    try:
        html = article_path.read_text(encoding="utf-8", errors="replace")
        prose = strip_scripts(html)
        prompt = PROMPT_TEMPLATE.format(
            quality_md=quality_md, article_path=rel, article_html=prose)

        result = subprocess.run(
            ["claude", "-p", "--model", model, "--output-format", "text",
             "--no-session-persistence"],
            input=prompt, capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            rep.error = f"claude exited {result.returncode}: {(result.stderr or '')[:300]}"
            return rep

        data = extract_json(result.stdout)
        for rule in M_RULES:
            v = data.get(rule, {})
            rep.verdicts.append(Verdict(
                rule=rule,
                status=str(v.get("status", "missing")).lower(),
                evidence=v.get("evidence", "")[:300],
                suggestion=v.get("suggestion", "")[:300],
            ))
        rep.overall = data.get("overall", "")[:600]
    except subprocess.TimeoutExpired:
        rep.error = f"claude timed out after {timeout}s"
    except Exception as e:
        rep.error = f"{type(e).__name__}: {e}"
    finally:
        rep.seconds = time.time() - started
    return rep


# ---------------------------------------------------------------------------
# Cache (per-article SHA → verdict)
# ---------------------------------------------------------------------------

def article_signature(path: Path) -> str:
    import hashlib
    return hashlib.sha1(path.read_bytes()).hexdigest()[:12]


def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

ICON = {"pass": "✓", "warn": "!", "fail": "✗", "missing": "?"}


def print_text(reports: List[Report]) -> int:
    fails = 0
    for r in reports:
        if r.error:
            print(f"\n✗ {r.path}  (ERROR: {r.error})")
            fails += 1
            continue
        # Summary line
        statuses = [v.status for v in r.verdicts]
        n_fail = statuses.count("fail")
        n_warn = statuses.count("warn")
        n_pass = statuses.count("pass")
        icon = "✗" if n_fail else ("!" if n_warn else "✓")
        print(f"\n{icon} {r.path}  ({n_pass} pass, {n_warn} warn, {n_fail} fail · {r.seconds:.1f}s)")
        for v in r.verdicts:
            if v.status == "pass":
                print(f"  ✓ [{v.rule}]  {v.evidence}")
            else:
                tag = ICON.get(v.status, "?")
                print(f"  {tag} [{v.rule}]  {v.evidence}")
                if v.suggestion:
                    print(f"        → {v.suggestion}")
        if r.overall:
            print(f"  ▸ {r.overall}")
        if n_fail:
            fails += 1

    print("\n" + "=" * 64)
    print(f"  Articles reviewed: {len(reports)}")
    print(f"  Articles with any fail: {fails}")
    print("=" * 64)
    return 1 if fails > 0 else 0


def print_json(reports: List[Report]) -> int:
    payload = []
    for r in reports:
        payload.append({
            "path": r.path,
            "seconds": r.seconds,
            "error": r.error,
            "overall": r.overall,
            "verdicts": [
                {"rule": v.rule, "status": v.status,
                 "evidence": v.evidence, "suggestion": v.suggestion}
                for v in r.verdicts
            ],
        })
    print(json.dumps(payload, indent=2))
    return 0 if not any(r.has_fail for r in reports) else 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="*", help="article folder or path; default = all")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--parallel", type=int, default=DEFAULT_PARALLELISM)
    ap.add_argument("--timeout", type=int, default=240)
    ap.add_argument("--cache", action="store_true",
                    help="skip articles whose content hash is already in .quality-cache.json")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if not QUALITY_MD.exists():
        print("QUALITY.md not found at repo root", file=sys.stderr)
        return 1
    quality_md = QUALITY_MD.read_text(encoding="utf-8")

    articles = find_articles()
    if args.targets:
        wanted = set(args.targets)
        articles = [a for a in articles
                    if a.parent.name in wanted or
                    a.relative_to(REPO_ROOT).as_posix().startswith(tuple(wanted))]
    if not articles:
        print("No articles match.", file=sys.stderr)
        return 1

    cache = load_cache() if args.cache else {}
    to_run: List[Path] = []
    cached_reports: List[Report] = []
    for a in articles:
        sig = article_signature(a)
        key = f"{a.relative_to(REPO_ROOT).as_posix()}@{sig}"
        if args.cache and key in cache:
            entry = cache[key]
            rep = Report(path=entry["path"], overall=entry.get("overall", ""),
                         seconds=entry.get("seconds", 0.0),
                         error=entry.get("error"))
            rep.verdicts = [Verdict(**v) for v in entry.get("verdicts", [])]
            cached_reports.append(rep)
        else:
            to_run.append(a)

    if not args.json and to_run:
        print(f"Evaluating {len(to_run)} article(s) with model={args.model}, "
              f"parallel={args.parallel}…\n", file=sys.stderr)

    fresh_reports: List[Report] = []
    if to_run:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = {pool.submit(evaluate, a, quality_md, args.model, args.timeout): a
                       for a in to_run}
            for fut in concurrent.futures.as_completed(futures):
                a = futures[fut]
                r = fut.result()
                fresh_reports.append(r)
                if not args.json:
                    n_fail = sum(1 for v in r.verdicts if v.status == "fail")
                    n_warn = sum(1 for v in r.verdicts if v.status == "warn")
                    if r.error:
                        print(f"  ✗ {r.path} — {r.error}", file=sys.stderr)
                    else:
                        print(f"  ✓ {r.path} — pass:{8 - n_fail - n_warn} warn:{n_warn} fail:{n_fail}",
                              file=sys.stderr)
                if args.cache:
                    sig = article_signature(a)
                    key = f"{a.relative_to(REPO_ROOT).as_posix()}@{sig}"
                    cache[key] = {
                        "path": r.path, "overall": r.overall,
                        "seconds": r.seconds, "error": r.error,
                        "verdicts": [v.__dict__ for v in r.verdicts],
                    }
        if args.cache:
            save_cache(cache)

    reports = cached_reports + fresh_reports
    reports.sort(key=lambda r: r.path)
    return print_json(reports) if args.json else print_text(reports)


if __name__ == "__main__":
    sys.exit(main())
