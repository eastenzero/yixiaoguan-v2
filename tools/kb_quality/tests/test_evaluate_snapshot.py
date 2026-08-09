from __future__ import annotations

import unittest

from tools.kb_quality.evaluate_snapshot import build_report


class SnapshotEvaluationTest(unittest.TestCase):
    def test_separates_exact_representation_stale_and_unavailable(self):
        dataset = {
            "record_type": "dataset",
            "id": "dataset-1",
            "name": "fixture",
            "created_at": "2026-01-01",
            "index_struct": {
                "vector_store": {"class_prefix": "Vector_index_fixture_Node"},
            },
        }

        def segment(segment_id: str, document_id: str, title: str, content: str, node_id: str):
            return {
                "record_type": "segment",
                "dataset_id": "dataset-1",
                "document_id": document_id,
                "document_name": title,
                "document_enabled": True,
                "document_archived": False,
                "document_indexing_status": "completed",
                "segment_id": segment_id,
                "segment_position": 1,
                "content": content,
                "index_node_id": node_id,
                "segment_enabled": True,
                "segment_status": "completed",
            }

        postgres_rows = [
            dataset,
            segment("s1", "d1", "重复正文一", "相同正文", "n1"),
            segment("s2", "d2", "重复正文二", "相同正文", "n2"),
            segment("s3", "d3", "VPN 使用指南", "连接 VPN 的步骤", "n3"),
        ]
        vector_rows = [
            {
                "collection": "Vector_index_fixture_Node",
                "object_id": "object-1",
                "properties": {"document_id": "d1", "doc_id": "n1", "text": "相同正文"},
            },
            {
                "collection": "Vector_index_fixture_Node",
                "object_id": "object-old",
                "properties": {"document_id": "d2", "doc_id": "old", "text": "旧正文"},
            },
        ]
        queries = [{"id": "Q1", "query": "VPN 怎么连接", "expected_any": ["VPN 使用指南"]}]

        report = build_report(postgres_rows, vector_rows, queries)["datasets"][0]
        self.assertEqual(report["index_exact_segments"], 1)
        self.assertEqual(report["index_content_represented_segments"], 2)
        self.assertEqual(report["index_unavailable_segments"], 1)
        self.assertEqual(report["stale_searchable_vectors"], 1)
        self.assertEqual(report["duplicate_content_groups"], 1)
        self.assertEqual(report["retrieval_ideal_source"]["hit_at_1"], 1.0)
        self.assertEqual(report["retrieval_actual_index"]["hit_at_1"], 0.0)


if __name__ == "__main__":
    unittest.main()
