#!/usr/bin/env python3
"""Evaluate an isolated Dify PostgreSQL + Weaviate snapshot.

The evaluator never connects to Dify. It measures source/index consistency and
runs a deterministic character-ngram BM25 retrieval check over both the ideal
active segment corpus and the actually searchable Weaviate objects.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


PLACEHOLDER_RE = re.compile(
    r"\[(?:待核实|待确认|待补充)\]|(?:TODO|TBD|FIXME)|(?:请以实际为准|具体[^。；\n]{0,12}待确认)",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"20(?:2[0-9])")
CHINESE_RUN_RE = re.compile(r"[\u3400-\u9fff]+")
ASCII_WORD_RE = re.compile(r"[a-z0-9]+")
QUERY_NOISE = {
    "怎么",
    "什么",
    "需要",
    "哪里",
    "哪儿",
    "哪些",
    "如何",
    "几个",
    "是否",
    "怎么办",
    "是什么",
}


@dataclass(frozen=True)
class CorpusItem:
    item_id: str
    document_id: str
    title: str
    text: str


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def read_jsonl(path: Path) -> Iterator[dict]:
    with open_text(path) as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc


def collection_name(dataset: dict) -> str:
    raw = dataset.get("index_struct")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = None
    if isinstance(raw, dict):
        value = (raw.get("vector_store") or {}).get("class_prefix")
        if value:
            return value if value.endswith("_Node") else f"{value}_Node"
    return f"Vector_index_{dataset['id'].replace('-', '_')}_Node"


def is_active(row: dict) -> bool:
    return bool(
        row.get("document_enabled")
        and not row.get("document_archived")
        and row.get("document_indexing_status") == "completed"
        and row.get("segment_enabled")
        and row.get("segment_status") == "completed"
    )


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def tokenize(text: str) -> list[str]:
    value = (text or "").lower()
    tokens = ASCII_WORD_RE.findall(value)
    for run in CHINESE_RUN_RE.findall(value):
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
        tokens.extend(run[index : index + 3] for index in range(len(run) - 2))
        if len(run) <= 8:
            tokens.append(run)
    return [token for token in tokens if token not in QUERY_NOISE]


class BM25:
    def __init__(self, items: list[CorpusItem], title_boost: int = 3):
        self.items = items
        self.term_frequencies: list[Counter[str]] = []
        self.document_frequencies: Counter[str] = Counter()
        self.lengths: list[int] = []
        for item in items:
            title_tokens = tokenize(item.title) * title_boost
            terms = title_tokens + tokenize(item.text)
            frequencies = Counter(terms)
            self.term_frequencies.append(frequencies)
            self.document_frequencies.update(frequencies)
            self.lengths.append(sum(frequencies.values()))
        self.average_length = sum(self.lengths) / len(self.lengths) if self.lengths else 1.0

    def search(self, query: str, limit: int = 6) -> list[tuple[float, CorpusItem]]:
        if not self.items:
            return []
        query_terms = set(tokenize(query))
        scored: list[tuple[float, CorpusItem]] = []
        total = len(self.items)
        for index, frequencies in enumerate(self.term_frequencies):
            score = 0.0
            length = self.lengths[index] or 1
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                document_frequency = self.document_frequencies[term]
                inverse_frequency = math.log(1 + (total - document_frequency + 0.5) / (document_frequency + 0.5))
                denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * length / self.average_length)
                score += inverse_frequency * frequency * 2.5 / denominator
            if score:
                scored.append((score, self.items[index]))
        scored.sort(key=lambda value: (-value[0], value[1].title, value[1].item_id))

        # Dify can return several chunks from one document. Collapse them here
        # so Hit@K represents K distinct source documents.
        collapsed: list[tuple[float, CorpusItem]] = []
        seen_documents: set[str] = set()
        for score, item in scored:
            if item.document_id in seen_documents:
                continue
            seen_documents.add(item.document_id)
            collapsed.append((score, item))
            if len(collapsed) == limit:
                break
        return collapsed


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9\u3400-\u9fff]+", "", (value or "").lower())


def expected_rank(results: list[tuple[float, CorpusItem]], expected: Iterable[str]) -> int | None:
    needles = [normalized(value) for value in expected]
    for rank, (_, item) in enumerate(results, 1):
        haystack = normalized(item.title)
        if any(needle and needle in haystack for needle in needles):
            return rank
    return None


def evaluate_retrieval(items: list[CorpusItem], queries: list[dict]) -> dict:
    model = BM25(items)
    ranks: list[int | None] = []
    details = []
    for query in queries:
        results = model.search(query["query"], limit=6)
        rank = expected_rank(results, query["expected_any"])
        ranks.append(rank)
        details.append(
            {
                "id": query["id"],
                "query": query["query"],
                "rank": rank,
                "top_titles": [item.title for _, item in results[:3]],
            }
        )
    total = len(ranks)
    return {
        "queries": total,
        "hit_at_1": sum(rank == 1 for rank in ranks) / total if total else 0.0,
        "hit_at_3": sum(rank is not None and rank <= 3 for rank in ranks) / total if total else 0.0,
        "hit_at_6": sum(rank is not None and rank <= 6 for rank in ranks) / total if total else 0.0,
        "mrr_at_6": sum(1 / rank for rank in ranks if rank is not None) / total if total else 0.0,
        "details": details,
    }


def build_report(postgres_rows: Iterable[dict], vector_rows: Iterable[dict], queries: list[dict]) -> dict:
    datasets: dict[str, dict] = {}
    segments_by_dataset: dict[str, list[dict]] = defaultdict(list)
    for row in postgres_rows:
        if row.get("record_type") == "dataset":
            datasets[row["id"]] = row
        elif row.get("record_type") == "segment":
            segments_by_dataset[row["dataset_id"]].append(row)

    vectors_by_collection: dict[str, list[dict]] = defaultdict(list)
    for row in vector_rows:
        vectors_by_collection[row["collection"]].append(row)

    result = {"evaluation_method": "offline character-ngram BM25", "datasets": []}
    for dataset_id, dataset in sorted(datasets.items(), key=lambda item: item[1].get("created_at") or ""):
        segments = segments_by_dataset.get(dataset_id, [])
        active_segments = [row for row in segments if is_active(row)]
        active_document_ids = {row["document_id"] for row in active_segments}
        active_index_node_ids = {row["index_node_id"] for row in active_segments if row.get("index_node_id")}
        collection = collection_name(dataset)
        vector_rows_for_dataset = vectors_by_collection.get(collection, [])

        searchable_vectors = [
            row
            for row in vector_rows_for_dataset
            if (row.get("properties") or {}).get("document_id") in active_document_ids
        ]
        searchable_doc_ids = {
            (row.get("properties") or {}).get("doc_id")
            for row in searchable_vectors
            if (row.get("properties") or {}).get("doc_id")
        }
        searchable_hashes = {
            content_hash((row.get("properties") or {}).get("text") or "") for row in searchable_vectors
        }
        exact_segments = [row for row in active_segments if row.get("index_node_id") in searchable_doc_ids]
        represented_segments = [
            row
            for row in active_segments
            if row.get("index_node_id") in searchable_doc_ids or content_hash(row.get("content") or "") in searchable_hashes
        ]
        stale_vectors = [
            row
            for row in searchable_vectors
            if (row.get("properties") or {}).get("doc_id") not in active_index_node_ids
        ]

        document_names = {row["document_id"]: row["document_name"] for row in segments}
        ideal_items = [
            CorpusItem(
                item_id=row["segment_id"],
                document_id=row["document_id"],
                title=row["document_name"],
                text=row.get("content") or "",
            )
            for row in active_segments
        ]
        actual_items = [
            CorpusItem(
                item_id=row.get("object_id") or "",
                document_id=(row.get("properties") or {}).get("document_id") or "",
                title=document_names.get((row.get("properties") or {}).get("document_id"), "<unknown>"),
                text=(row.get("properties") or {}).get("text") or "",
            )
            for row in searchable_vectors
        ]

        content_groups: dict[str, set[str]] = defaultdict(set)
        for row in active_segments:
            content_groups[content_hash(row.get("content") or "")].add(row["segment_id"])
        duplicate_groups = [ids for ids in content_groups.values() if len(ids) > 1]

        content_by_document: dict[str, list[str]] = defaultdict(list)
        for row in active_segments:
            content_by_document[row["document_id"]].append(row.get("content") or "")
        placeholder_documents = [
            document_id
            for document_id, content in content_by_document.items()
            if PLACEHOLDER_RE.search("\n".join(content))
        ]
        governance_fields = {
            "source_url": "source_url",
            "effective_status": "effective_status",
            "authority_level": "authority_level",
            "academic_year": "academic_year",
        }
        governance_coverage = {
            field: sum(marker in "\n".join(content) for content in content_by_document.values())
            for field, marker in governance_fields.items()
        }
        dated_documents = []
        for document_id, title in document_names.items():
            years = {int(year) for year in YEAR_RE.findall(title)}
            if document_id in active_document_ids and years and max(years) < 2026:
                dated_documents.append(document_id)

        active_count = len(active_segments)
        dataset_result = {
            "id": dataset_id,
            "name": dataset["name"],
            "collection": collection,
            "documents_total": len({row["document_id"] for row in segments}),
            "documents_active": len(active_document_ids),
            "segments_total": len(segments),
            "segments_active": active_count,
            "vectors_total": len(vector_rows_for_dataset),
            "vectors_searchable": len(searchable_vectors),
            "index_exact_segments": len(exact_segments),
            "index_exact_coverage": len(exact_segments) / active_count if active_count else 1.0,
            "index_content_represented_segments": len(represented_segments),
            "index_content_coverage": len(represented_segments) / active_count if active_count else 1.0,
            "index_unavailable_segments": active_count - len(represented_segments),
            "stale_searchable_vectors": len(stale_vectors),
            "object_id_matches_doc_id": sum(
                row.get("object_id") == (row.get("properties") or {}).get("doc_id")
                for row in vector_rows_for_dataset
            ),
            "duplicate_content_groups": len(duplicate_groups),
            "duplicate_content_segments": sum(len(ids) for ids in duplicate_groups),
            "placeholder_documents": len(placeholder_documents),
            "pre_2026_title_documents": len(dated_documents),
            "governance_document_counts": governance_coverage,
            "retrieval_ideal_source": evaluate_retrieval(ideal_items, queries),
            "retrieval_actual_index": evaluate_retrieval(actual_items, queries),
        }
        result["datasets"].append(dataset_result)
    return result


def print_summary(report: dict) -> None:
    header = (
        f"{'dataset':46} {'active':>7} {'exact%':>7} {'repr%':>7} "
        f"{'stale':>6} {'ideal@1':>8} {'actual@1':>9} {'actual@3':>9}"
    )
    print(header)
    print("-" * len(header))
    for item in report["datasets"]:
        print(
            f"{item['name'][:46]:46} {item['segments_active']:7d} "
            f"{item['index_exact_coverage'] * 100:6.1f}% "
            f"{item['index_content_coverage'] * 100:6.1f}% "
            f"{item['stale_searchable_vectors']:6d} "
            f"{item['retrieval_ideal_source']['hit_at_1'] * 100:7.1f}% "
            f"{item['retrieval_actual_index']['hit_at_1'] * 100:8.1f}% "
            f"{item['retrieval_actual_index']['hit_at_3'] * 100:8.1f}%"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--postgres", type=Path, required=True, help="PostgreSQL JSONL[.gz] snapshot")
    parser.add_argument("--weaviate", type=Path, required=True, help="Weaviate JSONL[.gz] snapshot")
    parser.add_argument(
        "--queries",
        type=Path,
        default=Path(__file__).with_name("golden_queries.jsonl"),
        help="golden query JSONL",
    )
    parser.add_argument("--output", type=Path, help="write full JSON report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(read_jsonl(args.postgres), read_jsonl(args.weaviate), list(read_jsonl(args.queries)))
    print_summary(report)
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
