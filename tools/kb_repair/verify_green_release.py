#!/usr/bin/env python3
"""Read-only release verifier for the selected green datasets and Shadow workflow."""

from __future__ import annotations

import copy
import hashlib
import json
import re

from app import app as flask_app
from extensions.ext_database import db
from models import App, ApiToken
from models.dataset import AppDatasetJoin, Dataset, DocumentSegment
from models.dataset import Document as DatasetDocument
from models.workflow import Workflow


FORMAL_APP_ID = "8cfaee92-f95c-4316-80a4-ab5d93614772"
FORMAL_WORKFLOW_ID = "f98baa82-d73f-44b0-aec5-de83078e8b37"
SHADOW_APP_ID = "76f7ba2c-5c61-47cb-a257-5800cf185e21"
R5_WORKFLOW_ID = "6f2b9a22-8a53-4e68-926c-901fdacac6af"
R7_WORKFLOW_ID = "882b1331-6721-4dbe-acca-9d630d0cad37"
DATASETS = {
    "main": ("a5732fe1-a85c-42a8-962c-2a4d8015b56a", 350, 740),
    "academic": ("6f8c8f85-9893-4036-b327-15c34ccb9aa5", 13, 55),
    "scholarship_standby": ("5a3c8e8f-b2b5-46b3-b350-f63c086c62de", 21, 145),
}


def node(graph: dict, node_id: str) -> dict:
    return next(value for value in graph["nodes"] if value["id"] == node_id)


def normalized_for_diff(graph: str) -> dict:
    value = copy.deepcopy(json.loads(graph))
    router = node(value, "1000000000003")
    router["data"]["cases"] = "<audited-routing-cases>"
    value["edges"] = [edge for edge in value["edges"] if edge["id"] != "edge-router-publicity-to-main"]
    return value


def main() -> None:
    checks: dict[str, bool] = {}
    evidence: dict = {}
    with flask_app.app_context():
        formal = db.session.get(App, FORMAL_APP_ID)
        shadow = db.session.get(App, SHADOW_APP_ID)
        r5 = db.session.get(Workflow, R5_WORKFLOW_ID)
        r7 = db.session.get(Workflow, R7_WORKFLOW_ID)
        if not all([formal, shadow, r5, r7]):
            raise SystemExit("required app/workflow missing")
        checks["formal_workflow_unchanged"] = formal.workflow_id == FORMAL_WORKFLOW_ID
        checks["formal_updated_at_unchanged"] = str(formal.updated_at) == "2026-08-04 15:13:01.412709"
        checks["shadow_points_to_r7"] = shadow.workflow_id == R7_WORKFLOW_ID
        checks["shadow_api_only"] = bool(shadow.enable_api) and not bool(shadow.enable_site)
        checks["formal_api_token_present"] = db.session.query(ApiToken).filter_by(app_id=formal.id).count() >= 1

        graph = json.loads(r7.graph)
        classifier = node(graph, "1000000000002")["data"]
        main_retrieval = node(graph, "1000000000030")["data"]
        main_llm = node(graph, "1000000000031")["data"]
        academic_retrieval = node(graph, "1000000000050")["data"]
        academic_llm = node(graph, "1000000000051")["data"]
        router = node(graph, "1000000000003")["data"]
        checks["qwen36_plus_everywhere"] = all(
            item["model"]["name"] == "qwen3.6-plus" for item in [classifier, main_llm, academic_llm]
        )
        checks["top6_rerank_everywhere"] = all(
            item["multiple_retrieval_config"]["top_k"] == 6
            and item["multiple_retrieval_config"]["reranking_model"]["model"] == "qwen3-rerank"
            for item in [main_retrieval, academic_retrieval]
        )
        checks["selected_datasets_only"] = (
            main_retrieval["dataset_ids"] == [DATASETS["main"][0]]
            and academic_retrieval["dataset_ids"] == [DATASETS["academic"][0]]
            and DATASETS["scholarship_standby"][0] not in r7.graph
        )
        checks["answer_limits_320"] = all(
            item["model"]["completion_params"]["max_tokens"] == 320 for item in [main_llm, academic_llm]
        )
        checks["deterministic_routes_present"] = {
            case["case_id"] for case in router["cases"]
        } == {"scholarship-publicity-main", "academic-keyword"}
        checks["r5_r7_diff_is_routing_only"] = normalized_for_diff(r5.graph) == normalized_for_diff(r7.graph)

        shadow_joins = {
            row.dataset_id for row in db.session.query(AppDatasetJoin).filter_by(app_id=SHADOW_APP_ID).all()
        }
        checks["shadow_dataset_joins_exact"] = shadow_joins == {DATASETS["main"][0], DATASETS["academic"][0]}

        dataset_evidence = {}
        for key, (dataset_id, expected_documents, expected_segments) in DATASETS.items():
            dataset = db.session.get(Dataset, dataset_id)
            documents = (
                db.session.query(DatasetDocument)
                .filter_by(dataset_id=dataset_id, enabled=True, archived=False, indexing_status="completed")
                .all()
            )
            segments = (
                db.session.query(DocumentSegment)
                .filter_by(dataset_id=dataset_id, enabled=True, status="completed")
                .all()
            )
            normalized = [re.sub(r"\s+", " ", segment.content).strip() for segment in segments]
            pending = (
                db.session.query(DocumentSegment)
                .filter(DocumentSegment.dataset_id == dataset_id, DocumentSegment.status != "completed")
                .count()
            )
            dataset_evidence[key] = {
                "id": dataset_id,
                "name": dataset.name if dataset else None,
                "documents": len(documents),
                "segments": len(segments),
                "pending": pending,
                "duplicate_normalized_content": len(normalized) - len(set(normalized)),
            }
            checks[f"{key}_database_shape"] = bool(dataset) and (
                len(documents), len(segments), pending, len(normalized) - len(set(normalized))
            ) == (expected_documents, expected_segments, 0, 0)

        evidence.update(
            {
                "formal": {
                    "app_id": formal.id,
                    "workflow_id": formal.workflow_id,
                    "updated_at": str(formal.updated_at),
                },
                "shadow": {
                    "app_id": shadow.id,
                    "workflow_id": shadow.workflow_id,
                    "graph_sha256": hashlib.sha256(r7.graph.encode()).hexdigest(),
                },
                "datasets": dataset_evidence,
            }
        )
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "evidence": evidence}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
