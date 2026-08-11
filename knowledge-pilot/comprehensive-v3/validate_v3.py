#!/usr/bin/env python3
"""校验 comprehensive-v3 治理包。"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
REQUIRED_FILES = {
    "README.md", "topic-taxonomy.json", "knowledge-card-schema.json", "answer-patterns.md",
    "clean_catalog.py", "catalog.jsonl", "topic-index.json", "quality-report.json",
    "evaluation.jsonl", "shadow-release.json",
    "curated-library-hours.json",
    "interaction-benchmark-v2.md",
}
VALID_STATUSES = {"answer_ready", "review_required", "context_only", "archive_only"}
VALID_ROLES = {"rule_evidence", "process_evidence", "result_context", "background_context"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    missing = REQUIRED_FILES - {path.name for path in ROOT.iterdir() if path.is_file()}
    assert not missing, f"missing files: {sorted(missing)}"

    cards = load_jsonl(ROOT / "catalog.jsonl")
    assert len(cards) >= 900, f"expected full catalog, got {len(cards)}"
    ids = [card["id"] for card in cards]
    assert len(ids) == len(set(ids)), "duplicate card ids"
    for card in cards:
        assert card["answer_status"] in VALID_STATUSES
        assert card["evidence_role"] in VALID_ROLES
        assert card["temporal_status"]
        assert card["content_quality"] in {"usable_excerpt", "page_chrome_polluted", "too_short"}
        assert card["title"] and card["source_owner"]
        parsed = urlparse(card["source_url"])
        assert parsed.scheme in {"http", "https"} and parsed.netloc, card["source_url"]

    topic_counts = Counter(card["topic"] for card in cards)
    assert len(topic_counts) >= 8, topic_counts
    assert topic_counts["awards_and_aid"] >= 80
    assert topic_counts["party_and_honors"] >= 80
    assert topic_counts["academic_affairs"] >= 60

    evaluations = load_jsonl(ROOT / "evaluation.jsonl")
    assert len(evaluations) >= 30
    assert len({item["id"] for item in evaluations}) == len(evaluations)
    for item in evaluations:
        assert item["min_chars"] >= 300
        assert item["min_paragraphs"] >= 3
        assert len(item["must_cover"]) >= 4

    report = json.loads((ROOT / "quality-report.json").read_text(encoding="utf-8"))
    assert report["deduplicated_count"] == len(cards)
    assert sum(report["answer_status"].values()) == len(cards)
    library_hours = json.loads((ROOT / "curated-library-hours.json").read_text(encoding="utf-8"))
    assert library_hours["facts"]["opens_at"] == "07:00"
    assert library_hours["facts"]["closes_at"] == "22:00"
    assert library_hours["facts"]["afternoon_open"] is True
    assert len(library_hours["common_questions"]) >= 5
    assert all("answer" in item for item in library_hours["common_questions"])
    assert len(library_hours["reference_materials"]) >= 2
    print(f"OK: {len(cards)} cards, {len(topic_counts)} topics, {len(evaluations)} evaluation cases")


if __name__ == "__main__":
    main()
