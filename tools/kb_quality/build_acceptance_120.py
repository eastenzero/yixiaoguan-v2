#!/usr/bin/env python3
"""Freeze the 62 existing questions plus 58 additions into one 120-case set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quality-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows: list[dict] = []
    for filename, route in [
        ("golden_queries.jsonl", "main"),
        ("academic_impact_queries.jsonl", "academic"),
        ("scholarship_queries.jsonl", "main"),
    ]:
        for row in read(args.quality_dir / filename):
            rows.append({**row, "route": route, "expected_outcome": "answer", "source_set": filename})
    rows.extend(read(args.quality_dir / "additional_acceptance_queries.jsonl"))
    if len(rows) != 120:
        raise SystemExit(f"acceptance set must contain 120 rows, found {len(rows)}")
    seen: set[str] = set()
    for index, row in enumerate(rows, 1):
        frozen_id = f"AC{index:03d}"
        original_id = row["id"]
        row["id"] = frozen_id
        row["original_id"] = original_id
        if frozen_id in seen:
            raise SystemExit(f"duplicate id: {frozen_id}")
        seen.add(frozen_id)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    print(json.dumps({"rows": len(rows), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
