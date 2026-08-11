#!/usr/bin/env python3
"""Minimal integrity checks for comprehensive answering v2."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REQUIRED = {
    "README.md",
    "answer-contract.md",
    "interaction-benchmark.md",
    "scholarship-matrix.json",
    "scholarship-longform.md",
    "evaluation.jsonl",
    "shadow-release.json",
}


def is_https(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    missing = sorted(name for name in REQUIRED if not (ROOT / name).is_file())
    assert not missing, f"missing files: {missing}"

    matrix = json.loads((ROOT / "scholarship-matrix.json").read_text(encoding="utf-8"))
    awards = matrix["awards"]
    ids = [award["id"] for award in awards]
    assert len(awards) >= 8 and len(ids) == len(set(ids)), "award cards are incomplete or duplicated"
    assert {award["level"] for award in awards} >= {"national", "provincial", "school", "college_or_social"}
    urls = [url for award in awards for url in award.get("source_urls", [])]
    assert urls and all(is_https(url) for url in urls), "invalid evidence URL"

    cases = []
    for line_number, line in enumerate((ROOT / "evaluation.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        assert case.get("query") and case.get("must_cover"), f"invalid case at line {line_number}"
        assert case.get("min_chars", 0) >= 200, f"v2 answer is still too short at line {line_number}"
        assert case.get("min_paragraphs", 0) >= 2, f"paragraph requirement missing at line {line_number}"
        cases.append(case)
    assert len(cases) >= 20, "evaluation set is too small"
    assert len({case["id"] for case in cases}) == len(cases), "duplicate evaluation ids"

    longform = (ROOT / "scholarship-longform.md").read_text(encoding="utf-8")
    for fact in ("10000", "6000", "5000", "1500", "4000", "互斥", "你现在怎么选"):
        assert fact in longform, f"longform example misses {fact}"
    assert len(longform) >= 1500, "longform example is not detailed enough"

    inherited_registry = ROOT.parent / "comprehensive-v1" / "source_registry.json"
    assert inherited_registry.is_file(), "v1 source registry is missing"
    print(f"OK: {len(awards)} award cards, {len(cases)} long-answer cases, {len(urls)} evidence links")


if __name__ == "__main__":
    main()
