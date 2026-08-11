import uuid
from types import SimpleNamespace

from core.rag.datasource.vdb.weaviate.weaviate_vector import WeaviateVector


vector = object.__new__(WeaviateVector)
first = str(uuid.uuid4())
second = str(uuid.uuid4())
documents = [
    SimpleNamespace(page_content="duplicate body", metadata={"doc_id": first}),
    SimpleNamespace(page_content="duplicate body", metadata={"doc_id": second}),
]
assert vector._get_uuids(documents) == [first, second]

fallback = [SimpleNamespace(page_content="legacy body", metadata={})]
expected = str(uuid.uuid5(uuid.NAMESPACE_URL, "legacy body"))
assert vector._get_uuids(fallback) == [expected]
print("weaviate_identity_patch=PASS")
