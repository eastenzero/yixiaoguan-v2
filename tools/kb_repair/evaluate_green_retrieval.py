#!/usr/bin/env python3
"""Evaluate green candidates through Dify semantic search plus qwen3-rerank."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from statistics import mean

import numpy as np

from app import app
from core.rag.datasource.retrieval_service import RetrievalService
from core.rag.retrieval.retrieval_methods import RetrievalMethod
from extensions.ext_database import db
from models.dataset import Document as DatasetDocument


RERANK = {
    "reranking_provider_name": "langgenius/tongyi/tongyi",
    "reranking_model_name": "qwen3-rerank",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", value.lower())


def rank_for(titles: list[str], expected: list[str]) -> int | None:
    needles = [normalized(value) for value in expected]
    for rank, title in enumerate(titles, 1):
        haystack = normalized(title)
        if any(needle and needle in haystack for needle in needles):
            return rank
    return None


def evaluate(dataset_id: str, queries: list[dict], checkpoint: Path, label: str) -> dict:
    document_names = dict(
        db.session.query(DatasetDocument.id, DatasetDocument.name)
        .filter_by(dataset_id=dataset_id)
        .all()
    )
    details = []
    for index, query in enumerate(queries, start=1):
        started = time.perf_counter()
        error = None
        try:
            results = RetrievalService.retrieve(
                retrieval_method=RetrievalMethod.SEMANTIC_SEARCH,
                dataset_id=dataset_id,
                query=query["query"],
                top_k=6,
                score_threshold=0,
                reranking_model=RERANK,
            )
            titles = [document_names.get(item.metadata.get("document_id"), "<unknown>") for item in results]
            scores = [round(float(item.metadata.get("score") or 0), 6) for item in results]
            rank = rank_for(titles, query["expected_any"])
        except Exception as exc:
            titles, scores, rank = [], [], None
            error = str(exc)
        latency = time.perf_counter() - started
        details.append(
            {
                "id": query["id"],
                "category": query.get("category"),
                "query": query["query"],
                "rank": rank,
                "latency_seconds": round(latency, 4),
                "top_titles": titles,
                "top_scores": scores,
                "error": error,
            }
        )
        checkpoint.write_text(json.dumps({"label": label, "details": details}, ensure_ascii=False, indent=2))
        print(f"eval label={label} query={index}/{len(queries)} rank={rank} latency={latency:.2f}s", flush=True)
    ranks = [item["rank"] for item in details]
    latencies = [item["latency_seconds"] for item in details]
    total = len(details)
    return {
        "dataset_id": dataset_id,
        "label": label,
        "queries": total,
        "hit_at_1": sum(rank == 1 for rank in ranks) / total,
        "hit_at_3": sum(rank is not None and rank <= 3 for rank in ranks) / total,
        "hit_at_6": sum(rank is not None and rank <= 6 for rank in ranks) / total,
        "mrr_at_6": sum(1 / rank for rank in ranks if rank is not None) / total,
        "errors": sum(item["error"] is not None for item in details),
        "latency_mean": mean(latencies),
        "latency_p95": float(np.percentile(latencies, 95)),
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--academic", type=Path, required=True)
    parser.add_argument("--scholarship", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    datasets = manifest["datasets"]
    suites = []
    for key, spec in datasets.items():
        name = spec.get("name", key)
        if "兼容候选" in name or "治理候选" in name or "主库" in name:
            suites.append((name + "/golden", spec["id"], read_jsonl(args.golden)))
            suites.append((name + "/scholarship", spec["id"], read_jsonl(args.scholarship)))
        elif "学业影响" in name:
            suites.append((name + "/academic", spec["id"], read_jsonl(args.academic)))
        elif "奖学金" in name:
            suites.append((name + "/scholarship", spec["id"], read_jsonl(args.scholarship)))

    report = {"rerank": RERANK, "top_k": 6, "suites": []}
    with app.app_context():
        for index, (label, dataset_id, queries) in enumerate(suites, start=1):
            checkpoint = args.artifacts / f"{args.output.stem}-suite-{index}.json"
            result = evaluate(dataset_id, queries, checkpoint, label)
            report["suites"].append(result)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
            print(
                f"suite={label} H1={result['hit_at_1']:.1%} H3={result['hit_at_3']:.1%} "
                f"MRR={result['mrr_at_6']:.3f} P95={result['latency_p95']:.2f}s errors={result['errors']}",
                flush=True,
            )


if __name__ == "__main__":
    main()
