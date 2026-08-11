#!/usr/bin/env python3
"""Apply or reverse the audited teacher KB document mapping with strict preflight."""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from pathlib import Path
from typing import Any


def psql(sql: str, *, csv_output: bool = False) -> str:
    command = ["docker", "exec", "-i", "yx_postgres", "psql", "-U", "yxg", "-d", "yixiaoguan_v2", "-X"]
    if csv_output:
        command.append("--csv")
    command.extend(["-v", "ON_ERROR_STOP=1"])
    result = subprocess.run(command, input=sql, check=True, capture_output=True, text=True)
    return result.stdout


def load_mapping(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text())
    rows = payload["mapped"]
    if len(rows) != payload["counts"]["mapped_business_entries"]:
        raise SystemExit("mapping count mismatch")
    return rows


def current_state(rows: list[dict[str, Any]]) -> dict[str, int]:
    ids = ",".join(str(int(row["kb_entry_id"])) for row in rows)
    output = psql(
        f"SELECT id::text AS kb_entry_id,dify_dataset_id,dify_document_id FROM kb_entries WHERE id IN ({ids}) ORDER BY id;",
        csv_output=True,
    )
    current = {row["kb_entry_id"]: row for row in csv.DictReader(io.StringIO(output))}
    result = {"old": 0, "new": 0, "other": 0, "missing": 0}
    for mapping in rows:
        row = current.get(str(mapping["kb_entry_id"]))
        if row is None:
            result["missing"] += 1
        elif (
            row["dify_dataset_id"] == mapping["old_dataset_id"]
            and row["dify_document_id"] == mapping["old_document_id"]
        ):
            result["old"] += 1
        elif (
            row["dify_dataset_id"] == mapping["new_dataset_id"]
            and row["dify_document_id"] == mapping["new_document_id"]
        ):
            result["new"] += 1
        else:
            result["other"] += 1
    return result


def copy_sql(rows: list[dict[str, Any]], mode: str) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    for row in rows:
        writer.writerow(
            [
                int(row["kb_entry_id"]),
                row["old_dataset_id"],
                row["old_document_id"],
                row["new_dataset_id"],
                row["new_document_id"],
            ]
        )
    if mode == "switch":
        source_dataset, source_document = "old_dataset_id", "old_document_id"
        target_dataset, target_document = "new_dataset_id", "new_document_id"
    else:
        source_dataset, source_document = "new_dataset_id", "new_document_id"
        target_dataset, target_document = "old_dataset_id", "old_document_id"
    return rf"""
BEGIN;
CREATE TEMP TABLE kbfix_mapping (
  kb_entry_id integer PRIMARY KEY,
  old_dataset_id text NOT NULL,
  old_document_id text NOT NULL,
  new_dataset_id text NOT NULL,
  new_document_id text NOT NULL
) ON COMMIT DROP;
COPY kbfix_mapping FROM STDIN WITH (FORMAT csv);
{buffer.getvalue()}\.
UPDATE kb_entries AS entry
SET dify_dataset_id = mapping.{target_dataset},
    dify_document_id = mapping.{target_document},
    updated_at = now()
FROM kbfix_mapping AS mapping
WHERE entry.id = mapping.kb_entry_id
  AND entry.dify_dataset_id = mapping.{source_dataset}
  AND entry.dify_document_id = mapping.{source_document};
COMMIT;
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["status", "switch", "rollback"])
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--confirm")
    args = parser.parse_args()
    expected = {
        "switch": "SWITCH_TEACHER_IDS_20260809",
        "rollback": "ROLLBACK_TEACHER_IDS_20260809",
    }
    rows = load_mapping(args.mapping)
    before = current_state(rows)
    if args.mode == "status":
        print(json.dumps({"mapped_rows": len(rows), "state": before}, ensure_ascii=False))
        return
    if args.confirm != expected[args.mode]:
        raise SystemExit(f"refusing {args.mode}: pass --confirm {expected[args.mode]}")
    if before["other"] or before["missing"]:
        raise SystemExit(f"mapping preflight failed: {before}")
    if args.mode == "switch" and before["old"] not in {0, len(rows)}:
        raise SystemExit(f"partial switch state: {before}")
    if args.mode == "rollback" and before["new"] not in {0, len(rows)}:
        raise SystemExit(f"partial rollback state: {before}")
    if (args.mode == "switch" and before["old"]) or (args.mode == "rollback" and before["new"]):
        psql(copy_sql(rows, args.mode))
    after = current_state(rows)
    expected_count = after["new"] if args.mode == "switch" else after["old"]
    if expected_count != len(rows) or after["other"] or after["missing"]:
        raise SystemExit(f"mapping postcheck failed: {after}")
    print(json.dumps({"mapped_rows": len(rows), "before": before, "after": after}, ensure_ascii=False))


if __name__ == "__main__":
    main()
