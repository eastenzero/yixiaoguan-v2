#!/usr/bin/env python3
"""Run an optional local semantic retrieval check over a read-only snapshot.

Dependency: ``fastembed``. Keep its model cache outside the repository, e.g.
``FASTEMBED_CACHE_PATH=/tmp/kb-model-cache``.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from evaluate_snapshot import (
    CorpusItem,
    collection_name,
    expected_rank,
    is_active,
    read_jsonl,
)


def snapshot_corpora(
    postgres_rows: list[dict], vector_rows: list[dict], corpus_mode: str
) -> dict[str, list[CorpusItem]]:
    datasets = {row["id"]: row for row in postgres_rows if row.get("record_type") == "dataset"}
    active_documents: dict[str, set[str]] = defaultdict(set)
    document_names: dict[str, str] = {}
    ideal_items: dict[str, list[CorpusItem]] = defaultdict(list)
    for row in postgres_rows:
        if row.get("record_type") != "segment":
            continue
        document_names[row["document_id"]] = row["document_name"]
        if is_active(row):
            active_documents[row["dataset_id"]].add(row["document_id"])
            ideal_items[row["dataset_id"]].append(
                CorpusItem(
                    item_id=row["segment_id"],
                    document_id=row["document_id"],
                    title=row["document_name"],
                    text=row.get("content") or "",
                )
            )

    if corpus_mode == "ideal":
        return {dataset["name"]: ideal_items.get(dataset_id, []) for dataset_id, dataset in datasets.items()}

    vectors_by_collection: dict[str, list[dict]] = defaultdict(list)
    for row in vector_rows:
        vectors_by_collection[row["collection"]].append(row)

    corpora: dict[str, list[CorpusItem]] = {}
    for dataset_id, dataset in datasets.items():
        items = []
        for row in vectors_by_collection.get(collection_name(dataset), []):
            properties = row.get("properties") or {}
            document_id = properties.get("document_id") or ""
            if document_id not in active_documents[dataset_id]:
                continue
            title = document_names.get(document_id, "<unknown>")
            items.append(
                CorpusItem(
                    item_id=row.get("object_id") or "",
                    document_id=document_id,
                    title=title,
                    text=properties.get("text") or "",
                )
            )
        corpora[dataset["name"]] = items
    return corpora


def unit_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return matrix / norms


def evaluate_dataset(
    model: TextEmbedding, items: list[CorpusItem], queries: list[dict], batch_size: int
) -> dict:
    passages = [f"{item.title}\n{item.text}" for item in items]
    passage_vectors = unit_rows(np.asarray(list(model.passage_embed(passages, batch_size=batch_size))))
    query_vectors = unit_rows(
        np.asarray(list(model.query_embed([query["query"] for query in queries], batch_size=batch_size)))
    )
    similarities = query_vectors @ passage_vectors.T
    ranks = []
    details = []
    for query_index, query in enumerate(queries):
        order = np.argsort(-similarities[query_index])
        results = []
        seen_documents = set()
        for item_index in order:
            item = items[int(item_index)]
            if item.document_id in seen_documents:
                continue
            seen_documents.add(item.document_id)
            results.append((float(similarities[query_index, item_index]), item))
            if len(results) == 6:
                break
        rank = expected_rank(results, query["expected_any"])
        ranks.append(rank)
        details.append(
            {
                "id": query["id"],
                "rank": rank,
                "top_titles": [item.title for _, item in results[:3]],
                "top_scores": [round(score, 6) for score, _ in results[:3]],
            }
        )
    total = len(queries)
    return {
        "queries": total,
        "hit_at_1": sum(rank == 1 for rank in ranks) / total,
        "hit_at_3": sum(rank is not None and rank <= 3 for rank in ranks) / total,
        "hit_at_6": sum(rank is not None and rank <= 6 for rank in ranks) / total,
        "mrr_at_6": sum(1 / rank for rank in ranks if rank is not None) / total,
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--postgres", type=Path, required=True)
    parser.add_argument("--weaviate", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--dataset", action="append", help="dataset name; repeat to compare several")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5")
    parser.add_argument(
        "--corpus",
        choices=("actual", "ideal"),
        default="actual",
        help="actual Weaviate objects or ideal active PostgreSQL segments",
    )
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    postgres_rows = list(read_jsonl(args.postgres))
    vector_rows = list(read_jsonl(args.weaviate))
    queries = list(read_jsonl(args.queries))
    corpora = snapshot_corpora(postgres_rows, vector_rows, args.corpus)
    requested = args.dataset or sorted(corpora)
    missing = [name for name in requested if name not in corpora]
    if missing:
        raise SystemExit(f"unknown datasets: {', '.join(missing)}")

    model = TextEmbedding(model_name=args.model, cache_dir=str(args.cache_dir) if args.cache_dir else None)
    report = {"model": args.model, "corpus": args.corpus, "datasets": []}
    for name in requested:
        metrics = evaluate_dataset(model, corpora[name], queries, args.batch_size)
        report["datasets"].append({"name": name, "items": len(corpora[name]), **metrics})
        print(
            f"{name}: items={len(corpora[name])} "
            f"Hit@1={metrics['hit_at_1']:.1%} Hit@3={metrics['hit_at_3']:.1%} "
            f"Hit@6={metrics['hit_at_6']:.1%} MRR@6={metrics['mrr_at_6']:.3f}"
        )
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
