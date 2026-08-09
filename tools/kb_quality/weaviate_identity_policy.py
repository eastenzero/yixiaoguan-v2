"""Proposed identity policy for Dify's Weaviate adapter.

The database ``index_node_id`` is stored in document metadata as ``doc_id`` and
is already a UUID in normal Dify indexing. Reusing it as the Weaviate object ID
makes insertion, existence checks, and deletion agree on one identity.
"""

from __future__ import annotations

import uuid
from typing import Any


URL_NAMESPACE = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")


def is_uuid(value: Any) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (TypeError, ValueError, AttributeError):
        return False


def object_id(page_content: str, metadata: dict[str, Any] | None = None) -> str:
    """Return an ID compatible with Dify's ``delete_by_ids(index_node_ids)``."""
    doc_id = (metadata or {}).get("doc_id")
    if is_uuid(doc_id):
        return str(doc_id)
    return str(uuid.uuid5(URL_NAMESPACE, page_content))


def object_ids(documents: list[Any]) -> list[str]:
    return [object_id(document.page_content, document.metadata) for document in documents]
