#!/usr/bin/env python3
"""Create idempotent green Dify datasets and freshly embed every green segment."""

from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from app import app
from core.entities.embedding_type import EmbeddingInputType
from core.model_manager import ModelManager
from core.rag.datasource.vdb.vector_factory import AbstractVectorFactory
from core.rag.datasource.vdb.vector_type import VectorType
from core.rag.datasource.vdb.weaviate.weaviate_vector import WeaviateVectorFactory
from core.rag.embedding.embedding_base import Embeddings
from core.rag.models.document import Document as RagDocument
from dify_graph.model_runtime.entities.model_entities import ModelPropertyKey, ModelType
from dify_graph.model_runtime.model_providers.__base.text_embedding_model import TextEmbeddingModel
from extensions.ext_database import db
from libs import helper
from models.dataset import Dataset, DatasetProcessRule, DocumentSegment
from models.dataset import Document as DatasetDocument


MAIN_ID = "4db0c819-7847-4a95-bf06-5b73a9d41d70"
ACADEMIC_ID = "47ee5e85-388d-4044-8c46-688b0ea3583a"
SCHOLARSHIP_ID = "97b99ca0-e253-4769-a915-a051a94611d8"
PROVIDER = "langgenius/tongyi/tongyi"
RUN_SUFFIX = "20260809"

OFFICIAL_CARDS = [
    {
        "key": "official:vpn",
        "title": "校外访问与 VPN：官方入口和技术支持",
        "content": (
            "【校外访问与 VPN｜官方入口】山东第一医科大学官网的信息门户页列出："
            "校内访问入口为 http://portal.sdfmu.edu.cn，校外访问入口为 "
            "http://vpnportal.sdfmu.edu.cn。登录方式、账号权限和可访问资源可能调整，"
            "请以页面实时提示为准。遇到问题请联系现代教育技术中心（网络信息中心）："
            "0531-59556211；技术支持电话 0531-59556212/6211、0538-6229861；"
            "邮箱 jyjs@sdfmu.edu.cn。不要使用来源不明的 VPN 客户端或代填账号。"
            "官方来源：https://www.sdfmu.edu.cn/xxmh.htm"
        ),
        "urls": ["https://www.sdfmu.edu.cn/xxmh.htm"],
    },
    {
        "key": "official:student-reimbursement-gap",
        "title": "学生报销：资料缺口与官方咨询入口",
        "content": (
            "【学生报销｜资料缺口】目前学校公开官网未检索到一份可确认适用于所有学生、"
            "所有经费来源和全部校区的统一报销操作细则，因此不提供票据种类、审批链、"
            "金额标准或截止时间等推测性结论。报销前请向经费负责人、所在学院办公室或"
            "学校财务处核实经费项目、审批人、所需附件和提交渠道；以财务系统实时要求"
            "及正式文件为准。学校官网确认财务处负责财务规章、资金收缴拨付和会计核算。"
            "官方机构页：https://www.sdfmu.edu.cn/info/1120/1602.htm"
        ),
        "urls": ["https://www.sdfmu.edu.cn/info/1120/1602.htm"],
    },
    {
        "key": "official:international-student-service-gap",
        "title": "外国留学生服务：官方咨询入口",
        "content": (
            "【外国留学生服务｜官方入口】国际教育学院是学校来华留学生教育负责部门，"
            "官网设有管理规定、签证服务、医疗保险、心理健康和常用表格等栏目。具体办理"
            "条件、材料、费用和时间以对应栏目最新通知为准；找不到明确规则时不要沿用"
            "历史草稿。学院地址：山东省泰安市长城路619号；邮箱 gjxy@sdfmu.edu.cn；"
            "学工办 +86-0538-6235751，后勤中心 +86-0538-6226819，院办/招办 "
            "+86-0538-6235860。官方来源：https://ie.sdfmu.edu.cn/"
        ),
        "urls": ["https://ie.sdfmu.edu.cn/", "https://ie.sdfmu.edu.cn/xygk/xyjj.htm"],
    },
]


def clone_values(model: type, source: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name == "id":
            continue
        values[column.name] = getattr(source, column.name)
    values.update(overrides)
    return values


def normalized_content(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_governance(path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            result[row["dify_document_id"]] = row
    return result


def retrieval_model(embedding_model: str) -> dict[str, Any]:
    return {
        "top_k": 6,
        "weights": {
            "weight_type": None,
            "vector_setting": {
                "vector_weight": None,
                "embedding_model_name": embedding_model,
                "embedding_provider_name": PROVIDER,
            },
            "keyword_setting": {"keyword_weight": 0.3},
        },
        "search_method": "semantic_search",
        "reranking_mode": "weighted_score",
        "reranking_model": {
            "reranking_model_name": "qwen3-rerank",
            "reranking_provider_name": PROVIDER,
        },
        "score_threshold": 0,
        "reranking_enable": True,
        "score_threshold_enabled": False,
    }


class FreshEmbedding(Embeddings):
    """Invoke the provider directly and deliberately bypass Dify's embedding cache."""

    def __init__(self, tenant_id: str, provider: str, model: str):
        self.model = ModelManager().get_model_instance(
            tenant_id=tenant_id,
            provider=provider,
            model_type=ModelType.TEXT_EMBEDDING,
            model=model,
        )
        model_type_instance = self.model.model_type_instance
        if not isinstance(model_type_instance, TextEmbeddingModel):
            raise TypeError(f"{model} is not a text embedding model")
        schema = model_type_instance.get_model_schema(self.model.model_name, self.model.credentials)
        self.max_chunks = int(
            schema.model_properties.get(ModelPropertyKey.MAX_CHUNKS, 1) if schema else 1
        )

    @staticmethod
    def normalize(vector: Any) -> list[float]:
        array = np.asarray(vector, dtype=float)
        norm = np.linalg.norm(array)
        if not norm or np.isnan(norm):
            raise ValueError("invalid embedding norm")
        normalized = array / norm
        if np.isnan(normalized).any():
            raise ValueError("embedding contains NaN")
        return normalized.tolist()

    def _invoke(self, texts: list[str], input_type: EmbeddingInputType) -> list[list[float]]:
        output: list[list[float]] = []
        for start in range(0, len(texts), self.max_chunks):
            result = self.model.invoke_text_embedding(
                texts=texts[start : start + self.max_chunks],
                user=None,
                input_type=input_type,
            )
            output.extend(self.normalize(vector) for vector in result.embeddings)
        if len(output) != len(texts):
            raise ValueError(f"embedding count mismatch: {len(output)} != {len(texts)}")
        return output

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._invoke(texts, EmbeddingInputType.DOCUMENT)

    def embed_query(self, text: str) -> list[float]:
        return self._invoke([text], EmbeddingInputType.QUERY)[0]

    def embed_multimodal_documents(self, multimodel_documents: list[dict]) -> list[list[float]]:
        raise NotImplementedError

    def embed_multimodal_query(self, multimodel_document: dict) -> list[float]:
        raise NotImplementedError


def get_or_create_dataset(
    source: Dataset,
    name: str,
    embedding_model: str,
    description: str,
) -> tuple[Dataset, bool]:
    existing = db.session.query(Dataset).filter_by(tenant_id=source.tenant_id, name=name).one_or_none()
    if existing:
        return existing, False
    dataset_id = str(uuid.uuid4())
    collection = Dataset.gen_collection_name_by_id(dataset_id)
    values = clone_values(
        Dataset,
        source,
        {
            "id": dataset_id,
            "name": name,
            "description": description,
            "embedding_model": embedding_model,
            "embedding_model_provider": PROVIDER,
            "retrieval_model": retrieval_model(embedding_model),
            "index_struct": json.dumps(
                AbstractVectorFactory.gen_index_struct_dict(VectorType.WEAVIATE, collection)
            ),
            "collection_binding_id": None,
            "pipeline_id": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        },
    )
    dataset = Dataset(**values)
    db.session.add(dataset)
    db.session.flush()
    source_rule = source.latest_process_rule
    if source_rule:
        rule = DatasetProcessRule(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            mode=source_rule.mode,
            rules=source_rule.rules,
            created_by=source_rule.created_by,
            created_at=datetime.now(),
        )
        db.session.add(rule)
    db.session.commit()
    return dataset, True


def active_documents(source_id: str) -> list[DatasetDocument]:
    return (
        db.session.query(DatasetDocument)
        .filter(
            DatasetDocument.dataset_id == source_id,
            DatasetDocument.indexing_status == "completed",
            DatasetDocument.enabled.is_(True),
            DatasetDocument.archived.is_(False),
        )
        .order_by(DatasetDocument.position, DatasetDocument.id)
        .all()
    )


def clone_documents(
    source: Dataset,
    target: Dataset,
    allowed_ids: set[str] | None,
    include_official_cards: bool,
) -> dict[str, Any]:
    existing_count = db.session.query(DatasetDocument).filter_by(dataset_id=target.id).count()
    mapping_path_key = target.name
    if existing_count:
        return {"target": target.id, "source": source.id, "existing": True, "mapping_key": mapping_path_key}

    target_rule = target.latest_process_rule
    selected = [doc for doc in active_documents(source.id) if allowed_ids is None or doc.id in allowed_ids]
    seen_content: set[str] = set()
    document_map: dict[str, str] = {}
    segment_map: dict[str, str] = {}
    position = 0

    for source_document in selected:
        source_segments = (
            db.session.query(DocumentSegment)
            .filter(
                DocumentSegment.document_id == source_document.id,
                DocumentSegment.enabled.is_(True),
                DocumentSegment.status == "completed",
            )
            .order_by(DocumentSegment.position, DocumentSegment.id)
            .all()
        )
        unique_segments: list[DocumentSegment] = []
        for source_segment in source_segments:
            normalized = normalized_content(source_segment.content)
            if not normalized or normalized in seen_content:
                continue
            seen_content.add(normalized)
            unique_segments.append(source_segment)
        if not unique_segments:
            continue

        position += 1
        document_id = str(uuid.uuid4())
        metadata = dict(source_document.doc_metadata or {})
        metadata.update(
            {
                "kbfix_source_document_id": source_document.id,
                "kbfix_source_dataset_id": source.id,
                "kbfix_green_dataset_id": target.id,
            }
        )
        document = DatasetDocument(
            **clone_values(
                DatasetDocument,
                source_document,
                {
                    "id": document_id,
                    "dataset_id": target.id,
                    "position": position,
                    "dataset_process_rule_id": target_rule.id if target_rule else None,
                    "batch": f"kbfix-green-{RUN_SUFFIX}",
                    "file_id": None,
                    "data_source_info": None,
                    "doc_metadata": metadata,
                    "word_count": sum(segment.word_count for segment in unique_segments),
                    "tokens": sum(segment.tokens for segment in unique_segments),
                    "processing_started_at": datetime.now(),
                    "parsing_completed_at": datetime.now(),
                    "cleaning_completed_at": datetime.now(),
                    "splitting_completed_at": datetime.now(),
                    "completed_at": datetime.now(),
                    "indexing_status": "completed",
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
        for segment_position, source_segment in enumerate(unique_segments, start=1):
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
                        "index_node_id": index_node_id,
                        "index_node_hash": helper.generate_text_hash(source_segment.content),
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

    if include_official_cards:
        template = selected[0]
        for card in OFFICIAL_CARDS:
            position += 1
            document_id = str(uuid.uuid4())
            document = DatasetDocument(
                **clone_values(
                    DatasetDocument,
                    template,
                    {
                        "id": document_id,
                        "dataset_id": target.id,
                        "position": position,
                        "dataset_process_rule_id": target_rule.id if target_rule else None,
                        "batch": f"kbfix-official-{RUN_SUFFIX}",
                        "name": card["title"],
                        "file_id": None,
                        "data_source_info": None,
                        "word_count": len(card["content"]),
                        "tokens": 0,
                        "indexing_latency": 0,
                        "indexing_status": "completed",
                        "enabled": True,
                        "archived": False,
                        "error": None,
                        "stopped_at": None,
                        "doc_metadata": {
                            "kbfix_source_document_id": card["key"],
                            "kbfix_official_urls": card["urls"],
                            "student_rag_visible": True,
                            "lifecycle_status": "published",
                            "rag_policy": "enable",
                            "freshness": "stable",
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
            index_node_id = str(uuid.uuid4())
            db.session.add(
                DocumentSegment(
                    id=str(uuid.uuid4()),
                    tenant_id=target.tenant_id,
                    dataset_id=target.id,
                    document_id=document_id,
                    position=1,
                    content=card["content"],
                    answer=None,
                    word_count=len(card["content"]),
                    tokens=0,
                    keywords=[],
                    index_node_id=index_node_id,
                    index_node_hash=helper.generate_text_hash(card["content"]),
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
            document_map[card["key"]] = document_id

    db.session.commit()
    return {
        "target": target.id,
        "source": source.id,
        "existing": False,
        "documents": document_map,
        "segments": segment_map,
        "mapping_key": mapping_path_key,
    }


def index_dataset(target: Dataset, artifacts: Path, batch_size: int = 32) -> dict[str, Any]:
    checkpoint_path = artifacts / f"checkpoint-{target.id}.json"
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {"indexed": []}
    indexed = set(checkpoint.get("indexed", []))
    fresh = FreshEmbedding(target.tenant_id, target.embedding_model_provider, target.embedding_model)
    processor = WeaviateVectorFactory().init_vector(
        target,
        ["doc_id", "dataset_id", "document_id", "doc_hash", "doc_type"],
        fresh,
    )
    segments = (
        db.session.query(DocumentSegment)
        .filter_by(dataset_id=target.id, enabled=True, status="completed")
        .order_by(DocumentSegment.document_id, DocumentSegment.position)
        .all()
    )
    pending: list[DocumentSegment] = []
    for segment in segments:
        if segment.index_node_id in indexed and processor.text_exists(segment.index_node_id):
            continue
        if processor.text_exists(segment.index_node_id):
            indexed.add(segment.index_node_id)
            continue
        pending.append(segment)

    for start in range(0, len(pending), batch_size):
        batch = pending[start : start + batch_size]
        rag_documents = [
            RagDocument(
                page_content=segment.content,
                metadata={
                    "doc_id": segment.index_node_id,
                    "doc_hash": segment.index_node_hash,
                    "document_id": segment.document_id,
                    "dataset_id": segment.dataset_id,
                    "doc_type": "text",
                },
            )
            for segment in batch
        ]
        delay = 5
        for attempt in range(1, 7):
            try:
                embeddings = fresh.embed_documents([document.page_content for document in rag_documents])
                processor.create(rag_documents, embeddings)
                break
            except Exception as error:
                if attempt == 6:
                    raise
                message = str(error).lower()
                if "429" not in message and "rate" not in message and "timeout" not in message:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 60)
        indexed.update(segment.index_node_id for segment in batch)
        checkpoint = {
            "dataset_id": target.id,
            "dataset_name": target.name,
            "indexed": sorted(indexed),
            "updated_at": datetime.now().isoformat(),
        }
        temporary = checkpoint_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2))
        temporary.replace(checkpoint_path)
        print(f"indexed dataset={target.id} completed={len(indexed)}/{len(segments)}", flush=True)
    return {"segments": len(segments), "indexed": len(indexed), "pending_before": len(pending)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--governance", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    governance = read_governance(args.governance)
    strict_ids = {
        document_id
        for document_id, row in governance.items()
        if row.get("lifecycle_status") == "published"
        and row.get("student_rag_visible") is True
        and row.get("rag_policy") != "exclude"
        and row.get("freshness") != "expired"
    }
    compat_ids = {
        document_id
        for document_id, row in governance.items()
        if row.get("lifecycle_status") == "published"
        and row.get("rag_policy") != "exclude"
        and row.get("freshness") != "expired"
    }

    with app.app_context():
        main_source = db.session.get(Dataset, MAIN_ID)
        academic_source = db.session.get(Dataset, ACADEMIC_ID)
        scholarship_source = db.session.get(Dataset, SCHOLARSHIP_ID)
        if not main_source or not academic_source or not scholarship_source:
            raise SystemExit("source dataset missing")

        definitions = [
            (
                main_source,
                f"医小管-GREEN-兼容候选-{RUN_SUFFIX}",
                "text-embedding-v4",
                compat_ids,
                True,
                "绿版兼容候选：仅正式发布、非 exclude、非过期；含官方资料缺口卡。",
            ),
            (
                main_source,
                f"医小管-GREEN-治理候选-{RUN_SUFFIX}",
                "text-embedding-v4",
                strict_ids,
                True,
                "绿版严格治理候选：student_rag_visible=true 且正式发布、非 exclude、非过期。",
            ),
            (
                academic_source,
                f"医小管-GREEN-学业影响-原embedding-{RUN_SUFFIX}",
                academic_source.embedding_model,
                None,
                False,
                "绿版学业影响 A/B：原 embedding，正文去重。",
            ),
            (
                academic_source,
                f"医小管-GREEN-学业影响-text-v4-{RUN_SUFFIX}",
                "text-embedding-v4",
                None,
                False,
                "绿版学业影响 A/B：text-embedding-v4，正文去重。",
            ),
            (
                scholarship_source,
                f"医小管-GREEN-奖学金-原embedding-{RUN_SUFFIX}",
                scholarship_source.embedding_model,
                None,
                False,
                "绿版奖学金精准备 A/B：原 embedding，正文去重。",
            ),
            (
                scholarship_source,
                f"医小管-GREEN-奖学金-text-v4-{RUN_SUFFIX}",
                "text-embedding-v4",
                None,
                False,
                "绿版奖学金精准备 A/B：text-embedding-v4，正文去重。",
            ),
        ]

        manifest: dict[str, Any] = {
            "run_suffix": RUN_SUFFIX,
            "created_at": datetime.now().isoformat(),
            "strict_allowed_documents": len(strict_ids),
            "compat_allowed_documents": len(compat_ids),
            "datasets": {},
        }
        mapping_path = args.artifacts / "green-id-mapping.json"
        mappings: dict[str, Any] = json.loads(mapping_path.read_text()) if mapping_path.exists() else {}
        for source, name, model, allowed, official, description in definitions:
            target, created = get_or_create_dataset(source, name, model, description)
            mapping = clone_documents(source, target, allowed, official)
            if not mapping.get("existing") or name not in mappings:
                mappings[name] = mapping
            index_result = index_dataset(target, args.artifacts)
            manifest["datasets"][name] = {
                "id": target.id,
                "source_id": source.id,
                "embedding_model": model,
                "created": created,
                **index_result,
            }
            (args.artifacts / "green-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2)
            )
            mapping_path.write_text(json.dumps(mappings, ensure_ascii=False, indent=2))

        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
