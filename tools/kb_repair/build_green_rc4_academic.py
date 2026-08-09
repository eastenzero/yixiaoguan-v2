#!/usr/bin/env python3
"""Build a final academic RC4 that resolves the single remaining A01 ranking miss."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app import app
from extensions.ext_database import db
from models.dataset import Dataset

from build_green_datasets import get_or_create_dataset, index_dataset
from build_green_rc3 import ALIASES, RENAMES, clone_candidate


SOURCE_ID = "4344a64a-0fd1-4879-8e0c-03b610453c0e"
TARGET_TITLE = "挂科一门是否影响入党｜党员发展规则边界"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    ALIASES["挂科对党员发展的上级规则边界"] = (
        "挂科一门是不是就不能入党；挂科一门是否影响入党；有一门不及格能不能入党；"
        "挂科对党员发展有什么影响；党员发展不把奖学金无不及格条件直接套用"
    )
    RENAMES["挂科对党员发展的上级规则边界"] = TARGET_TITLE
    with app.app_context():
        source = db.session.get(Dataset, SOURCE_ID)
        if source is None:
            raise SystemExit("missing academic RC3")
        target, created = get_or_create_dataset(
            source,
            "医小管-GREEN-RC4-学业影响最终候选-20260809",
            "text-embedding-v4",
            "学业影响 RC4：仅强化 A01 的明确问法别名，事实正文不变。",
        )
        mapping = clone_candidate(source, target)
        result = index_dataset(target, args.artifacts)
        manifest = {
            "created_at": datetime.now().isoformat(),
            "datasets": {
                "academic_final_rc4": {
                    "id": target.id,
                    "name": target.name,
                    "source_id": source.id,
                    "embedding_model": "text-embedding-v4",
                    "created": created,
                    **result,
                }
            },
        }
        (args.artifacts / "green-rc4-academic-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )
        (args.artifacts / "green-rc4-academic-id-mapping.json").write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2)
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
