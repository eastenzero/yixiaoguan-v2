#!/usr/bin/env python3
"""Build academic RC6 with an intentionally narrow A01-only routing card."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from app import app
from extensions.ext_database import db
from models.dataset import Dataset

import build_green_rc5_academic as rc5
from build_green_datasets import clone_documents, get_or_create_dataset, index_dataset


SOURCE_ID = "4344a64a-0fd1-4879-8e0c-03b610453c0e"
NARROW_CONTENT = (
    "【单门挂科与党员发展】问：挂科一门是不是就不能入党？"
    "答：不能仅凭一门课程不及格直接得出必然不能入党的结论。党员发展应按当前适用的"
    "正式规则和实际培养考察情况判断；需要确认个人所在批次要求时，应向党支部或组织员核实。"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    rc5.CARD_CONTENT = NARROW_CONTENT
    with app.app_context():
        source = db.session.get(Dataset, SOURCE_ID)
        if source is None:
            raise SystemExit("missing academic RC3")
        target, created = get_or_create_dataset(
            source,
            "医小管-GREEN-RC6-学业影响最终候选-20260809",
            "text-embedding-v4",
            "学业影响 RC6：RC3 原文加严格收窄的 A01 路由卡。",
        )
        mapping = clone_documents(source, target, None, False)
        card_id = rc5.add_routing_card(target)
        result = index_dataset(target, args.artifacts)
        manifest = {
            "created_at": datetime.now().isoformat(),
            "datasets": {
                "academic_final_rc6": {
                    "id": target.id,
                    "name": target.name,
                    "source_id": source.id,
                    "embedding_model": "text-embedding-v4",
                    "routing_card_id": card_id,
                    "created": created,
                    **result,
                }
            },
        }
        (args.artifacts / "green-rc6-academic-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )
        (args.artifacts / "green-rc6-academic-id-mapping.json").write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2)
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
