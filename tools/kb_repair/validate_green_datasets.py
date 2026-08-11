#!/usr/bin/env python3
"""Validate green Dify segment/vector coverage, identity and governance invariants."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import weaviate
from weaviate.classes.init import Auth

from app import app
from extensions.ext_database import db
from models.dataset import Dataset, DocumentSegment
from models.dataset import Document as DatasetDocument


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def governance_rows(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["dify_document_id"]] = row
    return rows


def connect_weaviate():
    endpoint = urlparse(os.environ["WEAVIATE_ENDPOINT"])
    grpc_value = os.environ.get("WEAVIATE_GRPC_ENDPOINT", "")
    grpc = urlparse(grpc_value if "://" in grpc_value else "grpc://" + grpc_value)
    return weaviate.connect_to_custom(
        http_host=endpoint.hostname or "weaviate",
        http_port=endpoint.port or 8080,
        http_secure=endpoint.scheme == "https",
        grpc_host=grpc.hostname or endpoint.hostname or "weaviate",
        grpc_port=grpc.port or 50051,
        grpc_secure=grpc.scheme == "grpcs",
        auth_credentials=Auth.api_key(os.environ["WEAVIATE_API_KEY"]),
        skip_init_checks=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--governance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    governance = governance_rows(args.governance)
    strict_allowed = {
        doc_id
        for doc_id, row in governance.items()
        if row.get("lifecycle_status") == "published"
        and row.get("student_rag_visible") is True
        and row.get("rag_policy") != "exclude"
        and row.get("freshness") != "expired"
    }
    compat_allowed = {
        doc_id
        for doc_id, row in governance.items()
        if row.get("lifecycle_status") == "published"
        and row.get("rag_policy") != "exclude"
        and row.get("freshness") != "expired"
    }
    report = {"result": "PASS", "datasets": {}}
    client = connect_weaviate()
    try:
        with app.app_context():
            for name, spec in manifest["datasets"].items():
                dataset = db.session.get(Dataset, spec["id"])
                if not dataset:
                    raise AssertionError(f"missing dataset {spec['id']}")
                documents = db.session.query(DatasetDocument).filter_by(dataset_id=dataset.id).all()
                segments = (
                    db.session.query(DocumentSegment)
                    .filter_by(dataset_id=dataset.id, enabled=True, status="completed")
                    .all()
                )
                node_ids = {segment.index_node_id for segment in segments}
                segment_ids = {segment.id for segment in segments}
                document_ids = {document.id for document in documents}
                source_ids = spec.get("source_ids") or [spec["source_id"]]
                source_documents = {
                    row[0]
                    for row in db.session.query(DatasetDocument.id)
                    .filter(DatasetDocument.dataset_id.in_(source_ids))
                    .all()
                }
                source_segments = {
                    row[0]
                    for row in db.session.query(DocumentSegment.id)
                    .filter(DocumentSegment.dataset_id.in_(source_ids))
                    .all()
                }
                source_nodes = {
                    row[0]
                    for row in db.session.query(DocumentSegment.index_node_id)
                    .filter(DocumentSegment.dataset_id.in_(source_ids))
                    .all()
                }
                collection_name = dataset.index_struct_dict["vector_store"]["class_prefix"]
                collection = client.collections.use(collection_name)
                object_ids: set[str] = set()
                property_doc_ids: set[str] = set()
                identity_mismatches = 0
                stale_vectors = 0
                wrong_dataset_metadata = 0
                vectorless = 0
                for obj in collection.iterator(include_vector=True):
                    object_id = str(obj.uuid)
                    properties = dict(obj.properties or {})
                    property_doc_id = str(properties.get("doc_id") or "")
                    object_ids.add(object_id)
                    property_doc_ids.add(property_doc_id)
                    identity_mismatches += int(object_id != property_doc_id)
                    stale_vectors += int(property_doc_id not in node_ids)
                    wrong_dataset_metadata += int(str(properties.get("dataset_id")) != dataset.id)
                    vector = obj.vector
                    if isinstance(vector, dict):
                        vector = vector.get("default") or next(iter(vector.values()), None)
                    vectorless += int(not vector)

                bodies = [normalize(segment.content) for segment in segments]
                duplicate_bodies = len(bodies) - len(set(bodies))
                pending_markers = sum(
                    bool(re.search(r"\[待核实\]|【待核实】|\[草稿\]|【草稿】|活动待核实", segment.content))
                    for segment in segments
                )
                unauthorized_sources = 0
                display_name = dataset.name
                if "兼容候选" in display_name or "治理候选" in display_name:
                    allowed = strict_allowed if "治理候选" in display_name else compat_allowed
                    for document in documents:
                        source_id = (document.doc_metadata or {}).get("kbfix_source_document_id")
                        rc2_source_dataset = (document.doc_metadata or {}).get(
                            "kbfix_rc2_source_dataset_id"
                        )
                        if str(source_id).startswith("official:"):
                            urls = (document.doc_metadata or {}).get("kbfix_official_urls") or []
                            unauthorized_sources += sum(
                                not (urlparse(url).hostname or "").endswith("sdfmu.edu.cn") for url in urls
                            )
                        elif rc2_source_dataset in source_ids[1:]:
                            # RC2 main intentionally merges a canonical green standby library.
                            pass
                        elif source_id not in allowed:
                            unauthorized_sources += 1

                checks = {
                    "db_documents": len(documents),
                    "db_segments": len(segments),
                    "vector_objects": len(object_ids),
                    "missing_object_uuid": len(node_ids - object_ids),
                    "missing_doc_id_property": len(node_ids - property_doc_ids),
                    "stale_vectors": stale_vectors,
                    "identity_mismatches": identity_mismatches,
                    "wrong_dataset_metadata": wrong_dataset_metadata,
                    "vectorless": vectorless,
                    "duplicate_bodies": duplicate_bodies,
                    "pending_markers": pending_markers,
                    "unauthorized_sources": unauthorized_sources,
                    "reused_document_ids": len(document_ids & source_documents),
                    "reused_segment_ids": len(segment_ids & source_segments),
                    "reused_index_node_ids": len(node_ids & source_nodes),
                }
                failures = {
                    key: value
                    for key, value in checks.items()
                    if key
                    in {
                        "missing_object_uuid",
                        "missing_doc_id_property",
                        "stale_vectors",
                        "identity_mismatches",
                        "wrong_dataset_metadata",
                        "vectorless",
                        "duplicate_bodies",
                        "pending_markers",
                        "unauthorized_sources",
                        "reused_document_ids",
                        "reused_segment_ids",
                        "reused_index_node_ids",
                    }
                    and value != 0
                }
                if len(object_ids) != len(segments):
                    failures["object_count_mismatch"] = len(object_ids) - len(segments)
                checks["result"] = "FAIL" if failures else "PASS"
                checks["failures"] = failures
                report["datasets"][name] = checks
                if failures:
                    report["result"] = "FAIL"
    finally:
        client.close()
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
