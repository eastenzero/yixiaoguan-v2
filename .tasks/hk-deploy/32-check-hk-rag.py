#!/usr/bin/env python3
import json
import urllib.request
from collections import Counter

DSID = "c2363fef-405b-48ab-a0e2-9274a4186cef"
DATASET_KEY = "dataset-Cw9zcTBywGSgBAlivhRrKn6k"
APP_KEY = "app-mhFlKWSXuLeWF24IB8J6JhXR"
BASE = "http://127.0.0.1:8088/v1"


def get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def post_json(url, headers, body):
    data = json.dumps(body, ensure_ascii=False).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())


def check_indexing():
    headers = {"Authorization": f"Bearer {DATASET_KEY}"}
    ds = get_json(f"{BASE}/datasets/{DSID}", headers)
    print(f"embedding_model: {ds.get('embedding_model')}")
    print(f"embedding_provider: {ds.get('embedding_model_provider')}")

    status = Counter()
    pages = 0
    for page in range(1, 30):
        docs = get_json(f"{BASE}/datasets/{DSID}/documents?page={page}&limit=100", headers).get("data", [])
        if not docs:
            break
        pages += 1
        for doc in docs:
            status[doc.get("indexing_status", "?")] += 1

    total = sum(status.values())
    print(f"total_docs_scanned: {total} pages={pages}")
    for key, count in sorted(status.items()):
        print(f"  {key}: {count} ({count / total * 100:.1f}%)")
    return status


def test_rag(query):
    headers = {
        "Authorization": f"Bearer {APP_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "inputs": {
            "college_name": "临床与基础医学院",
            "campus": "济南校区",
            "class_name": "临床2024-1班",
        },
        "query": query,
        "response_mode": "blocking",
        "user": "hk-rag-check",
    }
    print("\n=== QUERY ===")
    print(query)
    data = post_json(f"{BASE}/chat-messages", headers, body)
    print("--- answer ---")
    print((data.get("answer") or "")[:900])
    print("--- retriever_resources ---")
    for i, item in enumerate(data.get("metadata", {}).get("retriever_resources", []), 1):
        print(f"#{i} score={item.get('score', 0):.4f} doc={item.get('document_name', '?')[:70]}")
        print(f"   content={item.get('content', '')[:140]}")


status = check_indexing()
if status and status.get("completed", 0) == sum(status.values()):
    test_rag("宿舍电费怎么交？支付方式有哪些？")
    test_rag("请问国家奖学金有哪些类型？金额多少？怎么申请？")
    test_rag("校医院在哪？开放时间？有哪些科室？")
else:
    print("\nindexing_not_finished; skip rag tests")
