#!/bin/bash
# Debug retrieval: hit-testing API to see top-K for various queries.
# Also search for specific docs by name to verify they're indexed.
DATASET="c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE="http://127.0.0.1:8088/v1"

echo "=== TEST 1: hit-testing for 电费 ==="
python3 - <<'PY'
import json, urllib.request
DATASET="c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE="http://127.0.0.1:8088/v1"
url = f"{BASE}/datasets/{DATASET}/hit-testing"
req = urllib.request.Request(
    url,
    data=json.dumps({"query": "宿舍电费怎么交？支付方式有哪些？", "retrieval_model": {"search_method": "semantic_search", "reranking_enable": False, "top_k": 10, "score_threshold_enabled": False}}).encode(),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
except Exception as e:
    print(f"err: {e}")
    raise SystemExit(1)
records = body.get("records", [])
print(f"got {len(records)} records")
for i, rec in enumerate(records, 1):
    seg = rec.get("segment", {})
    doc = seg.get("document", {})
    print(f"\n#{i} score={rec.get('score'):.4f}  doc='{doc.get('name')}'")
    print(f"   content[0:150]: {seg.get('content', '')[:150]}")
PY

echo
echo
echo "=== TEST 2: search for KB-0150 explicitly ==="
python3 - <<'PY'
import json, urllib.request
DATASET="c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE="http://127.0.0.1:8088/v1"
# list with keyword
url = f"{BASE}/datasets/{DATASET}/documents?keyword=电费&page=1&limit=20"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}"})
with urllib.request.urlopen(req, timeout=20) as r:
    body = json.loads(r.read())
print(f"docs containing '电费': {body.get('total')}")
for d in body.get("data", [])[:10]:
    print(f"  - {d.get('name')[:50]:50}  status={d.get('indexing_status')}  segments=?")

print()
url2 = f"{BASE}/datasets/{DATASET}/documents?keyword=KB-0150&page=1&limit=5"
req = urllib.request.Request(url2, headers={"Authorization": f"Bearer {KEY}"})
with urllib.request.urlopen(req, timeout=20) as r:
    body = json.loads(r.read())
print(f"\ndocs matching 'KB-0150': {body.get('total')}")
for d in body.get("data", []):
    print(f"  - id={d.get('id')}  name={d.get('name')}")
PY

echo
echo "=== TEST 3: hit-testing with keyword search (BM25) instead of semantic ==="
python3 - <<'PY'
import json, urllib.request
DATASET="c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE="http://127.0.0.1:8088/v1"
url = f"{BASE}/datasets/{DATASET}/hit-testing"
req = urllib.request.Request(
    url,
    data=json.dumps({
        "query": "宿舍电费缴纳",
        "retrieval_model": {
            "search_method": "full_text_search",
            "reranking_enable": False,
            "top_k": 10,
            "score_threshold_enabled": False
        }
    }).encode(),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read())
    records = body.get("records", [])
    print(f"full-text search got {len(records)} records")
    for i, rec in enumerate(records, 1):
        seg = rec.get("segment", {})
        doc = seg.get("document", {})
        print(f"#{i} score={rec.get('score', 0):.4f}  doc='{doc.get('name')}'  content={seg.get('content','')[:100]}")
except Exception as e:
    print(f"err: {e}")
PY
