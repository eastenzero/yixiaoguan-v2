#!/usr/bin/env python3
"""Build academic RC5 from RC3 plus one narrow, non-factual intent-routing card."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from app import app
from extensions.ext_database import db
from libs import helper
from models.dataset import Dataset, DocumentSegment
from models.dataset import Document as DatasetDocument

from build_green_datasets import clone_documents, clone_values, get_or_create_dataset, index_dataset


SOURCE_ID = "4344a64a-0fd1-4879-8e0c-03b610453c0e"
CARD_TITLE = "挂科对党员发展的上级规则边界"
CARD_CONTENT = (
    "【单项党员发展问题路由】问题：挂科一门是不是就不能入党？"
    "结论边界：不能仅凭一门课程不及格直接推断一定不能入党，也不能把某项奖学金或评优的"
    "“无不及格”条件套用为党员发展条件。应分别核对上级党员发展规则和本学院当前批次细则；"
    "学院细则未公开时，明确资料缺口并向学院党委、组织员或党支部核实。"
    "本卡只处理单项党员发展边界；同时询问奖学金、评优等多个事项时，应转到多事项拆分矩阵分别判断。"
)


def add_routing_card(target: Dataset) -> str:
    existing = (
        db.session.query(DatasetDocument)
        .filter_by(dataset_id=target.id, batch="kbfix-academic-routing-rc5")
        .one_or_none()
    )
    if existing:
        return existing.id
    template = (
        db.session.query(DatasetDocument)
        .filter_by(dataset_id=target.id)
        .order_by(DatasetDocument.position)
        .first()
    )
    if template is None:
        raise RuntimeError("target has no template document")
    max_position = max(
        position
        for (position,) in db.session.query(DatasetDocument.position).filter_by(dataset_id=target.id).all()
    )
    document_id = str(uuid.uuid4())
    target_rule = target.latest_process_rule
    document = DatasetDocument(
        **clone_values(
            DatasetDocument,
            template,
            {
                "id": document_id,
                "dataset_id": target.id,
                "position": max_position + 1,
                "dataset_process_rule_id": target_rule.id if target_rule else None,
                "batch": "kbfix-academic-routing-rc5",
                "name": CARD_TITLE,
                "file_id": None,
                "data_source_info": None,
                "word_count": len(CARD_CONTENT),
                "tokens": 0,
                "indexing_status": "completed",
                "indexing_latency": 0,
                "enabled": True,
                "archived": False,
                "error": None,
                "stopped_at": None,
                "doc_metadata": {
                    "kbfix_source_document_id": "routing:academic-party-single",
                    "kbfix_source_dataset_id": SOURCE_ID,
                    "kbfix_green_dataset_id": target.id,
                    "kbfix_card_type": "intent-routing-boundary",
                },
                "processing_started_at": datetime.now(),
                "parsing_completed_at": datetime.now(),
                "cleaning_completed_at": datetime.now(),
                "splitting_completed_at": datetime.now(),
                "completed_at": datetime.now(),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        )
    )
    db.session.add(document)
    content = CARD_CONTENT
    db.session.add(
        DocumentSegment(
            id=str(uuid.uuid4()),
            tenant_id=target.tenant_id,
            dataset_id=target.id,
            document_id=document_id,
            position=1,
            content=content,
            answer=None,
            word_count=len(content),
            tokens=0,
            keywords=[],
            index_node_id=str(uuid.uuid4()),
            index_node_hash=helper.generate_text_hash(content),
            hit_count=0,
            enabled=True,
            status="completed",
            created_by=target.created_by,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            indexing_at=datetime.now(),
            completed_at=datetime.now(),
        )
    )
    db.session.commit()
    return document_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    with app.app_context():
        source = db.session.get(Dataset, SOURCE_ID)
        if source is None:
            raise SystemExit("missing academic RC3")
        target, created = get_or_create_dataset(
            source,
            "医小管-GREEN-RC5-学业影响最终候选-20260809",
            "text-embedding-v4",
            "学业影响 RC5：RC3 原文加单项党员发展边界路由卡。",
        )
        mapping = clone_documents(source, target, None, False)
        card_id = add_routing_card(target)
        result = index_dataset(target, args.artifacts)
        manifest = {
            "created_at": datetime.now().isoformat(),
            "datasets": {
                "academic_final_rc5": {
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
        (args.artifacts / "green-rc5-academic-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)
        )
        (args.artifacts / "green-rc5-academic-id-mapping.json").write_text(
            json.dumps(mapping, ensure_ascii=False, indent=2)
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
