#!/usr/bin/env python3
"""Build isolated RC2 candidates without mutating the first green candidates."""

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
from models.dataset import Dataset, DatasetProcessRule, DocumentSegment
from models.dataset import Document as DatasetDocument

from build_green_datasets import clone_values, get_or_create_dataset, index_dataset


RUN_SUFFIX = "20260809"

COMPAT_GREEN = "0305ea16-3383-487d-a336-51a54962cb3d"
ACADEMIC_ORIGINAL_GREEN = "60559f30-bf52-4594-b47f-a6de38c12eb4"
ACADEMIC_V4_GREEN = "d64d2b0f-c69b-4446-be23-e6f157c27a8e"
SCHOLARSHIP_ORIGINAL_GREEN = "a2f14f39-0df2-42f1-91d8-5a1aee1623b8"
SCHOLARSHIP_V4_GREEN = "1cb5f957-d28d-4796-974c-eaa05bd63a68"


OFFICIAL_ROUTING_CARDS = [
    {
        "key": "official:transfer-major-2026",
        "title": "转专业申请流程：2026年官方实施办法入口",
        "content": (
            "山东第一医科大学信息公开网已发布《普通本科学生转专业实施办法》。"
            "转专业条件、计划数、申请时间、材料和学院考核要求应以当年度教务通知及该办法为准；"
            "不同专业容量和考核安排可能不同，不沿用历史草稿。官方入口："
            "https://information.sdfmu.edu.cn/info/1033/17698.htm"
        ),
        "urls": ["https://information.sdfmu.edu.cn/info/1033/17698.htm"],
    },
    {
        "key": "official:psychological-consultation-gap",
        "title": "心理咨询服务指南：官方咨询与预约入口",
        "content": (
            "学校学生工作部职责包括大学生心理健康教育和咨询工作。公开官网未发现一份可确认"
            "当前对所有校区均适用的统一预约步骤，因此不沿用旧通知中的时段、地点或账号。"
            "请从学生工作部官网或所在学院辅导员核实当前预约入口；紧急或有即时伤害风险时应立即"
            "联系当地急救、警方或就近医疗机构。官方入口：https://sa.sdfmu.edu.cn/index.htm"
        ),
        "urls": ["https://sa.sdfmu.edu.cn/index.htm", "https://sa.sdfmu.edu.cn/bmjs/bmzz.htm"],
    },
    {
        "key": "official:international-exchange-current",
        "title": "国际交流项目与出国交换：官方项目入口",
        "content": (
            "学生出国交换、短期访学和海外交流项目由山东第一医科大学对外合作交流部持续发布。"
            "项目名单、对象、语言要求、费用、学分认定和截止时间按具体项目最新通知执行。"
            "学生交流入口：https://icd.sdfmu.edu.cn/xsjl.htm；咨询电话 0531-59556928，"
            "邮箱 wsb@sdfmu.edu.cn。"
        ),
        "urls": ["https://icd.sdfmu.edu.cn/xsjl.htm"],
    },
    {
        "key": "official:discipline-appeal",
        "title": "学生纪律处分规定与处分申诉官方入口",
        "content": (
            "学校《普通本科学生管理规定》确认学生对处理或处分决定不服可以提出申诉，"
            "由学生申诉处理委员会受理，具体程序以现行学生申诉处理办法和处分决定随附告知为准。"
            "不要依据非正式摘要推断期限或材料；可先联系所在学院或学生工作部。官方规定："
            "https://sps.sdfmu.edu.cn/info/1039/2270.htm；学生工作部：https://sa.sdfmu.edu.cn/"
        ),
        "urls": ["https://sps.sdfmu.edu.cn/info/1039/2270.htm", "https://sa.sdfmu.edu.cn/"],
    },
    {
        "key": "official:student-aid-work-study",
        "title": "助学贷款与勤工助学：学生工作部官方入口",
        "content": (
            "助学贷款、困难认定、奖助学金和勤工助学由学校学生工作部发布通知并组织实施。"
            "申请条件、岗位、材料和截止时间以学生工作部当期通知为准；历史通知只用于理解流程，"
            "不能替代当前要求。官方入口：https://sa.sdfmu.edu.cn/index.htm；规章制度："
            "https://sa.sdfmu.edu.cn/gzzd.htm"
        ),
        "urls": ["https://sa.sdfmu.edu.cn/index.htm", "https://sa.sdfmu.edu.cn/gzzd.htm"],
    },
    {
        "key": "official:innovation-project",
        "title": "大创项目申报指南与大学生创新创业官方入口",
        "content": (
            "大学生创新创业训练计划项目和相关申报通知由学校教务部发布。项目批次、申报对象、"
            "团队要求、材料和截止时间以教务部当期公告及项目平台为准，不沿用过期竞赛通知。"
            "官方入口：https://jwc.sdfmu.edu.cn/"
        ),
        "urls": ["https://jwc.sdfmu.edu.cn/"],
    },
    {
        "key": "official:school-overview",
        "title": "学校概况与校区分布：山东第一医科大学官方入口",
        "content": (
            "学校校区、地址、机构设置和联系方式可能随建设调整。查询有几个校区、校区地址或"
            "学院所在校区时，应以山东第一医科大学官网的学校概况、机构设置和页面底部联系信息"
            "为准。官方入口：https://www.sdfmu.edu.cn/xxgk1/xxjj.htm"
        ),
        "urls": ["https://www.sdfmu.edu.cn/xxgk1/xxjj.htm"],
    },
    {
        "key": "official:lab-safety",
        "title": "实验室安全规范与官方管理入口",
        "content": (
            "进入实验室前应完成所在单位要求的安全教育和准入，遵守实验室现场标识、操作规程、"
            "个人防护和危险品管理要求。不同实验室风险不同，具体规则以实验室负责人、所在学院"
            "及学校国有资产与实验室管理部门的现行制度为准；发现事故隐患应停止相关操作并报告。"
            "学校官网：https://www.sdfmu.edu.cn/"
        ),
        "urls": ["https://www.sdfmu.edu.cn/"],
    },
]


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def active_documents(dataset_id: str) -> list[DatasetDocument]:
    return (
        db.session.query(DatasetDocument)
        .filter_by(dataset_id=dataset_id, enabled=True, archived=False, indexing_status="completed")
        .order_by(DatasetDocument.position, DatasetDocument.id)
        .all()
    )


def make_document(
    target: Dataset,
    template: DatasetDocument,
    name: str,
    position: int,
    metadata: dict[str, Any],
    word_count: int,
    tokens: int,
) -> DatasetDocument:
    target_rule = target.latest_process_rule
    document = DatasetDocument(
        **clone_values(
            DatasetDocument,
            template,
            {
                "id": str(uuid.uuid4()),
                "dataset_id": target.id,
                "name": name,
                "position": position,
                "dataset_process_rule_id": target_rule.id if target_rule else None,
                "batch": f"kbfix-green-rc2-{RUN_SUFFIX}",
                "file_id": None,
                "data_source_info": None,
                "doc_metadata": metadata,
                "word_count": word_count,
                "tokens": tokens,
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
    return document


def add_segment(
    target: Dataset,
    document: DatasetDocument,
    content: str,
    position: int,
    template: DocumentSegment | None,
) -> tuple[str, str]:
    segment_id = str(uuid.uuid4())
    index_node_id = str(uuid.uuid4())
    overrides = {
        "id": segment_id,
        "tenant_id": target.tenant_id,
        "dataset_id": target.id,
        "document_id": document.id,
        "position": position,
        "content": content,
        "answer": None,
        "word_count": len(content),
        "tokens": 0,
        "keywords": [],
        "index_node_id": index_node_id,
        "index_node_hash": helper.generate_text_hash(content),
        "hit_count": 0,
        "enabled": True,
        "status": "completed",
        "created_by": target.created_by,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "indexing_at": datetime.now(),
        "completed_at": datetime.now(),
        "error": None,
        "stopped_at": None,
    }
    if template:
        segment = DocumentSegment(**clone_values(DocumentSegment, template, overrides))
    else:
        segment = DocumentSegment(**overrides)
    db.session.add(segment)
    return segment_id, index_node_id


def clone_with_title_prefix(
    sources: list[Dataset],
    target: Dataset,
    include_routing_cards: bool,
) -> dict[str, Any]:
    existing = db.session.query(DatasetDocument).filter_by(dataset_id=target.id).count()
    if existing:
        return {"existing": True, "documents": existing}

    seen_body: set[str] = set()
    mappings: dict[str, str] = {}
    segment_mappings: dict[str, str] = {}
    position = 0
    first_template: DatasetDocument | None = None

    for source in sources:
        for source_document in active_documents(source.id):
            if first_template is None:
                first_template = source_document
            source_segments = (
                db.session.query(DocumentSegment)
                .filter_by(document_id=source_document.id, enabled=True, status="completed")
                .order_by(DocumentSegment.position, DocumentSegment.id)
                .all()
            )
            chosen: list[tuple[DocumentSegment, str]] = []
            for source_segment in source_segments:
                body = normalized(source_segment.content)
                if not body or body in seen_body:
                    continue
                seen_body.add(body)
                content = f"【{source_document.name}】\n{source_segment.content}"
                chosen.append((source_segment, content))
            if not chosen:
                continue
            position += 1
            metadata = dict(source_document.doc_metadata or {})
            metadata.update(
                {
                    "kbfix_rc2_source_document_id": source_document.id,
                    "kbfix_rc2_source_dataset_id": source.id,
                    "kbfix_green_dataset_id": target.id,
                    "kbfix_title_prefixed": True,
                }
            )
            document = make_document(
                target,
                source_document,
                source_document.name,
                position,
                metadata,
                sum(len(content) for _, content in chosen),
                0,
            )
            mappings[f"{source.id}:{source_document.id}"] = document.id
            for segment_position, (source_segment, content) in enumerate(chosen, 1):
                segment_id, _ = add_segment(target, document, content, segment_position, source_segment)
                segment_mappings[f"{source.id}:{source_segment.id}"] = segment_id

    if include_routing_cards:
        if first_template is None:
            raise RuntimeError("cannot add cards without a document template")
        for card in OFFICIAL_ROUTING_CARDS:
            position += 1
            metadata = {
                "kbfix_source_document_id": card["key"],
                "kbfix_official_urls": card["urls"],
                "student_rag_visible": True,
                "lifecycle_status": "published",
                "rag_policy": "enable",
                "freshness": "stable",
                "kbfix_title_prefixed": True,
            }
            content = f"【{card['title']}】\n{card['content']}"
            document = make_document(
                target, first_template, card["title"], position, metadata, len(content), 0
            )
            add_segment(target, document, content, 1, None)
            mappings[card["key"]] = document.id

    db.session.commit()
    return {
        "existing": False,
        "documents": mappings,
        "segments": segment_mappings,
        "unique_source_bodies": len(seen_body),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        datasets = {
            dataset_id: db.session.get(Dataset, dataset_id)
            for dataset_id in [
                COMPAT_GREEN,
                ACADEMIC_ORIGINAL_GREEN,
                ACADEMIC_V4_GREEN,
                SCHOLARSHIP_ORIGINAL_GREEN,
                SCHOLARSHIP_V4_GREEN,
            ]
        }
        missing = [dataset_id for dataset_id, dataset in datasets.items() if dataset is None]
        if missing:
            raise SystemExit(f"missing green source datasets: {missing}")

        definitions = [
            (
                "main_compatible_rc2",
                [datasets[COMPAT_GREEN], datasets[SCHOLARSHIP_V4_GREEN]],
                "医小管-GREEN-RC2-主库兼容候选-20260809",
                "text-embedding-v4",
                True,
                "RC2 主库：首轮兼容候选加奖学金卡，标题前缀重嵌入及官网入口补齐。",
            ),
            (
                "academic_original_rc2",
                [datasets[ACADEMIC_ORIGINAL_GREEN]],
                "医小管-GREEN-RC2-学业影响-原embedding-20260809",
                datasets[ACADEMIC_ORIGINAL_GREEN].embedding_model,
                False,
                "RC2 学业影响原 embedding：标题前缀重嵌入。",
            ),
            (
                "academic_v4_rc2",
                [datasets[ACADEMIC_V4_GREEN]],
                "医小管-GREEN-RC2-学业影响-text-v4-20260809",
                "text-embedding-v4",
                False,
                "RC2 学业影响 text-v4：标题前缀重嵌入。",
            ),
            (
                "scholarship_original_rc2",
                [datasets[SCHOLARSHIP_ORIGINAL_GREEN]],
                "医小管-GREEN-RC2-奖学金-原embedding-20260809",
                datasets[SCHOLARSHIP_ORIGINAL_GREEN].embedding_model,
                False,
                "RC2 奖学金原 embedding：标题前缀重嵌入。",
            ),
            (
                "scholarship_v4_rc2",
                [datasets[SCHOLARSHIP_V4_GREEN]],
                "医小管-GREEN-RC2-奖学金-text-v4-20260809",
                "text-embedding-v4",
                False,
                "RC2 奖学金 text-v4：标题前缀重嵌入。",
            ),
        ]

        manifest: dict[str, Any] = {
            "run_suffix": RUN_SUFFIX,
            "created_at": datetime.now().isoformat(),
            "datasets": {},
        }
        mappings: dict[str, Any] = {}
        for key, sources, name, model, cards, description in definitions:
            target, created = get_or_create_dataset(sources[0], name, model, description)
            mapping = clone_with_title_prefix(sources, target, cards)
            index_result = index_dataset(target, args.artifacts)
            mappings[key] = mapping
            manifest["datasets"][key] = {
                "id": target.id,
                "name": target.name,
                "source_ids": [source.id for source in sources],
                "embedding_model": model,
                "created": created,
                **index_result,
            }
            (args.artifacts / "green-rc2-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2)
            )
            (args.artifacts / "green-rc2-id-mapping.json").write_text(
                json.dumps(mappings, ensure_ascii=False, indent=2)
            )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
