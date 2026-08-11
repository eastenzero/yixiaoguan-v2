#!/usr/bin/env python3
"""Export the reversible teacher KB old/new Dify document mapping on tx-new."""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


OLD_MAIN_DATASET_ID = "4db0c819-7847-4a95-bf06-5b73a9d41d70"
NEW_MAIN_DATASET_ID = "a5732fe1-a85c-42a8-962c-2a4d8015b56a"


def query(container: str, user: str, database: str, sql: str) -> list[dict[str, str]]:
    result = subprocess.run(
        [
            "docker",
            "exec",
            container,
            "psql",
            "-U",
            user,
            "-d",
            database,
            "-X",
            "--csv",
            "-c",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return list(csv.DictReader(io.StringIO(result.stdout)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    green_rows = query(
        "docker-db_postgres-1",
        "postgres",
        "dify",
        f"""
        SELECT
          doc_metadata->>'kbfix_source_document_id' AS old_document_id,
          id AS new_document_id,
          name AS new_document_name
        FROM documents
        WHERE dataset_id = '{NEW_MAIN_DATASET_ID}'
        ORDER BY id
        """,
    )
    entries = query(
        "yx_postgres",
        "yxg",
        "yixiaoguan_v2",
        """
        SELECT
          id::text AS kb_entry_id,
          dify_dataset_id AS old_dataset_id,
          dify_document_id AS old_document_id,
          title,
          lifecycle_status,
          student_rag_visible::text AS student_rag_visible
        FROM kb_entries
        ORDER BY id
        """,
    )

    green_by_old = {
        row["old_document_id"]: row
        for row in green_rows
        if row.get("old_document_id") and len(row["old_document_id"]) == 36
    }
    mapped = []
    unmatched = []
    for entry in entries:
        target = green_by_old.get(entry["old_document_id"])
        if target is None:
            unmatched.append(entry)
            continue
        mapped.append(
            {
                **entry,
                "new_dataset_id": NEW_MAIN_DATASET_ID,
                "new_document_id": target["new_document_id"],
                "new_document_name": target["new_document_name"],
            }
        )

    duplicate_old_ids = sorted(
        old_id
        for old_id in {row["old_document_id"] for row in green_rows}
        if sum(row["old_document_id"] == old_id for row in green_rows) > 1
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_main_dataset_id": OLD_MAIN_DATASET_ID,
        "new_main_dataset_id": NEW_MAIN_DATASET_ID,
        "counts": {
            "green_documents": len(green_rows),
            "green_uuid_source_documents": len(green_by_old),
            "business_entries": len(entries),
            "mapped_business_entries": len(mapped),
            "unmatched_business_entries": len(unmatched),
            "duplicate_green_old_document_ids": len(duplicate_old_ids),
        },
        "duplicate_green_old_document_ids": duplicate_old_ids,
        "mapped": mapped,
        "unmatched": unmatched,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
