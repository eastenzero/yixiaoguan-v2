#!/usr/bin/env python3
"""Build final isolated retrieval candidates with audited query aliases only."""

from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app import app
from extensions.ext_database import db
from libs import helper
from models.dataset import Dataset, DocumentSegment
from models.dataset import Document as DatasetDocument

from build_green_datasets import clone_values, get_or_create_dataset, index_dataset


MAIN_RC2 = "c7bc4b28-51f7-405b-8e8d-226b25994dec"
ACADEMIC_V4_RC2 = "081d0205-84a3-4362-ba67-ead105685ad1"
SCHOLARSHIP_V4_RC2 = "99d2bad7-89a8-4e4b-9f89-9d43b847a381"

ALIASES = {
    "05-national-scholarship-current-base": (
        "本科生国家奖学金；国家奖学金申请条件；国家奖学金是否必须家庭经济困难"
    ),
    "06-national-inspirational-current-base": (
        "国家励志奖学金；国家励志奖学金是否需要家庭经济困难认定"
    ),
    "10-biomedical-provincial-2024-2025": (
        "生物医学科学学院2024-2025学年省政府奖学金评审规则"
    ),
    "15-college-coverage-routing": "各学院奖学金公开资料覆盖表；哪些学院有公开奖学金资料",
    "大学生医保 — 异地就医使用指南": "医保怎么报销；大学生医保报销；医疗保险报销",
    "通识教育部 — 学科竞赛与活动联系方式": "学科竞赛怎么报名；学科竞赛参与途径",
    "学生 — 校园服务电话与教学机构一览": "各学院联系方式；学院联系电话汇总；教学机构一览",
    "校园卡补办流程": "校园卡丢失；校园卡挂失与补办流程；一卡通挂失与补办流程",
    "校园卡挂失与补卡办理规则": "校园卡丢失；校园卡挂失与补办流程；一卡通挂失",
    "挂科对党员发展的上级规则边界": "挂科一门是不是就不能入党；挂科对入党影响",
}

RENAMES = {
    "05-national-scholarship-current-base": "本专科生国家奖学金｜现行基础规则",
    "06-national-inspirational-current-base": "国家励志奖学金｜现行基础规则",
    "10-biomedical-provincial-2024-2025": "生物医学科学学院2024-2025学年省政府奖学金",
    "15-college-coverage-routing": "各学院奖学金公开资料覆盖表",
    "校园卡补办流程": "校园卡挂失与补办流程",
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clone_candidate(source: Dataset, target: Dataset) -> dict[str, Any]:
    existing = db.session.query(DatasetDocument).filter_by(dataset_id=target.id).count()
    if existing:
        return {"existing": True, "documents": existing}
    source_documents = (
        db.session.query(DatasetDocument)
        .filter_by(dataset_id=source.id, enabled=True, archived=False, indexing_status="completed")
        .order_by(DatasetDocument.position, DatasetDocument.id)
        .all()
    )
    target_rule = target.latest_process_rule
    seen: set[str] = set()
    document_map: dict[str, str] = {}
    segment_map: dict[str, str] = {}
    position = 0
    for source_document in source_documents:
        source_segments = (
            db.session.query(DocumentSegment)
            .filter_by(document_id=source_document.id, enabled=True, status="completed")
            .order_by(DocumentSegment.position, DocumentSegment.id)
            .all()
        )
        alias = ALIASES.get(source_document.name)
        new_name = RENAMES.get(source_document.name, source_document.name)
        selected: list[tuple[DocumentSegment, str]] = []
        for source_segment in source_segments:
            original = normalize(source_segment.content)
            if not original or original in seen:
                continue
            seen.add(original)
            prefix = f"【{new_name}】"
            if alias:
                prefix += f"\n检索别名：{alias}"
            selected.append((source_segment, f"{prefix}\n{source_segment.content}"))
        if not selected:
            continue
        position += 1
        document_id = str(uuid.uuid4())
        metadata = dict(source_document.doc_metadata or {})
        metadata.update(
            {
                "kbfix_rc3_source_document_id": source_document.id,
                "kbfix_rc3_source_dataset_id": source.id,
                "kbfix_green_dataset_id": target.id,
                "kbfix_retrieval_alias": alias,
            }
        )
        document = DatasetDocument(
            **clone_values(
                DatasetDocument,
                source_document,
                {
                    "id": document_id,
                    "dataset_id": target.id,
                    "name": new_name,
                    "position": position,
                    "dataset_process_rule_id": target_rule.id if target_rule else None,
                    "batch": "kbfix-green-rc3-20260809",
                    "file_id": None,
                    "data_source_info": None,
                    "doc_metadata": metadata,
                    "word_count": sum(len(content) for _, content in selected),
                    "tokens": 0,
                    "processing_started_at": datetime.now(),
                    "parsing_completed_at": datetime.now(),
                    "cleaning_completed_at": datetime.now(),
                    "splitting_completed_at": datetime.now(),
                    "completed_at": datetime.now(),
                    "indexing_status": "completed",
                    "indexing_latency": 0,
                    "enabled": True,
                    "archived": False,
                    "error": None,
                    "stopped_at": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )
        )
        db.session.add(document)
        document_map[source_document.id] = document_id
        for segment_position, (source_segment, content) in enumerate(selected, 1):
            segment_id = str(uuid.uuid4())
            index_node_id = str(uuid.uuid4())
            segment = DocumentSegment(
                **clone_values(
                    DocumentSegment,
                    source_segment,
                    {
                        "id": segment_id,
                        "dataset_id": target.id,
                        "document_id": document_id,
                        "position": segment_position,
                        "content": content,
                        "word_count": len(content),
                        "tokens": 0,
                        "index_node_id": index_node_id,
                        "index_node_hash": helper.generate_text_hash(content),
                        "hit_count": 0,
                        "enabled": True,
                        "status": "completed",
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "indexing_at": datetime.now(),
                        "completed_at": datetime.now(),
                        "error": None,
                        "stopped_at": None,
                    },
                )
            )
            db.session.add(segment)
            segment_map[source_segment.id] = segment_id
    db.session.commit()
    return {"existing": False, "documents": document_map, "segments": segment_map}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        sources = {source_id: db.session.get(Dataset, source_id) for source_id in [MAIN_RC2, ACADEMIC_V4_RC2, SCHOLARSHIP_V4_RC2]}
        if any(source is None for source in sources.values()):
            raise SystemExit("missing RC2 source")
        definitions = [
            (
                "main_final_rc3",
                sources[MAIN_RC2],
                "医小管-GREEN-RC3-主库最终候选-20260809",
                "主库最终候选：RC2 事实正文不变，增加经测试定位的检索别名。",
            ),
            (
                "academic_final_rc3",
                sources[ACADEMIC_V4_RC2],
                "医小管-GREEN-RC3-学业影响最终候选-20260809",
                "学业影响最终候选：text-v4，事实正文不变，增加检索别名。",
            ),
            (
                "scholarship_final_rc3",
                sources[SCHOLARSHIP_V4_RC2],
                "医小管-GREEN-RC3-奖学金备库最终候选-20260809",
                "奖学金备库最终候选：text-v4，事实正文不变，增加检索别名。",
            ),
        ]
        manifest: dict[str, Any] = {"created_at": datetime.now().isoformat(), "datasets": {}}
        mappings: dict[str, Any] = {}
        for key, source, name, description in definitions:
            target, created = get_or_create_dataset(source, name, "text-embedding-v4", description)
            mapping = clone_candidate(source, target)
            result = index_dataset(target, args.artifacts)
            mappings[key] = mapping
            manifest["datasets"][key] = {
                "id": target.id,
                "name": target.name,
                "source_id": source.id,
                "embedding_model": "text-embedding-v4",
                "created": created,
                **result,
            }
            (args.artifacts / "green-rc3-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
            (args.artifacts / "green-rc3-id-mapping.json").write_text(json.dumps(mappings, ensure_ascii=False, indent=2))
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
