#!/usr/bin/env python3
"""Validate the comprehensive knowledge pack with the standard library only."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REQUIRED = {
    "README.md",
    "answer-contract.md",
    "source_registry.json",
    "scholarship-guide.md",
    "retrieval-policy.json",
    "evaluation.jsonl",
    "github-design-notes.md",
    "comparison-preview.md",
    "shadow-release.json",
}


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def main() -> None:
    missing = sorted(name for name in REQUIRED if not (ROOT / name).is_file())
    assert not missing, f"missing files: {missing}"

    registry = json.loads((ROOT / "source_registry.json").read_text(encoding="utf-8"))
    sources = registry["sources"]
    ids = [source["id"] for source in sources]
    assert len(ids) == len(set(ids)), "duplicate source ids"
    assert len(sources) >= 25, "source registry is too narrow"
    assert all(valid_url(source["url"]) for source in sources), "invalid or non-HTTPS source URL"
    scopes = {source["scope"] for source in sources}
    assert {"national", "provincial", "school", "college"} <= scopes, "missing policy level"

    cases = []
    for line_number, line in enumerate((ROOT / "evaluation.jsonl").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        case = json.loads(line)
        assert case.get("id") and case.get("query"), f"invalid evaluation case at line {line_number}"
        assert case.get("must_cover"), f"missing must_cover at line {line_number}"
        cases.append(case)
    assert len(cases) >= 20, "evaluation set is too small"
    assert len({case["id"] for case in cases}) == len(cases), "duplicate evaluation ids"

    guide = (ROOT / "scholarship-guide.md").read_text(encoding="utf-8")
    for label in ("国家层面", "山东省层面", "学校层面", "学院层面"):
        assert label in guide, f"scholarship guide is missing {label}"

    print(f"OK: {len(sources)} sources, {len(cases)} evaluation cases, 4 scholarship levels")


if __name__ == "__main__":
    main()
