from __future__ import annotations

import unittest
from dataclasses import dataclass, field

from tools.kb_quality.weaviate_identity_policy import object_ids


@dataclass
class Document:
    page_content: str
    metadata: dict = field(default_factory=dict)


class WeaviateIdentityPolicyTest(unittest.TestCase):
    def test_duplicate_content_keeps_distinct_segment_ids(self):
        first = "11111111-1111-4111-8111-111111111111"
        second = "22222222-2222-4222-8222-222222222222"
        documents = [
            Document("相同内容", {"doc_id": first}),
            Document("相同内容", {"doc_id": second}),
        ]
        self.assertEqual(object_ids(documents), [first, second])

    def test_object_id_is_the_id_used_by_delete_by_ids(self):
        segment_id = "33333333-3333-4333-8333-333333333333"
        self.assertEqual(object_ids([Document("正文", {"doc_id": segment_id})]), [segment_id])

    def test_legacy_fallback_remains_deterministic(self):
        documents = [Document("无合法 doc_id"), Document("无合法 doc_id", {"doc_id": "not-a-uuid"})]
        first, second = object_ids(documents)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
