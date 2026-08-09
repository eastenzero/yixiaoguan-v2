from pathlib import Path


TARGET = Path("/app/api/core/rag/datasource/vdb/weaviate/weaviate_vector.py")
OLD = """        uuids = []
        for doc in documents:
            uuid_val = _uuid.uuid5(URL_NAMESPACE, doc.page_content)
            uuids.append(str(uuid_val))

        return uuids
"""
NEW = """        uuids = []
        for doc in documents:
            # Dify persists this value as document_segments.index_node_id and
            # passes it back to delete_by_ids(). Reusing it here keeps object
            # creation and deletion on the same identity and prevents equal
            # chunk text from overwriting another segment's metadata.
            doc_id = (doc.metadata or {}).get(\"doc_id\")
            if doc_id and self._is_uuid(str(doc_id)):
                uuids.append(str(doc_id))
            else:
                uuids.append(str(_uuid.uuid5(URL_NAMESPACE, doc.page_content)))

        return uuids
"""


source = TARGET.read_text()
occurrences = source.count(OLD)
if occurrences != 1:
    raise SystemExit(f"expected exactly one unpatched block, found {occurrences}")
TARGET.write_text(source.replace(OLD, NEW))
