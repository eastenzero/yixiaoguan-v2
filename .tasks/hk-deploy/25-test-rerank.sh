#!/bin/bash
# Test rerank: hit-testing with rerank enabled, top_k=10
python3 - <<'PY'
import json, urllib.request, urllib.error
DATASET="c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE="http://127.0.0.1:8088/v1"

queries = [
    "宿舍电费怎么交？支付方式有哪些？",
    "请问国家奖学金有哪些类型？金额多少？怎么申请？",
    "校医院在哪？开放时间？有哪些科室？",
]

for q in queries:
    print(f"\n{'='*80}")
    print(f"QUERY: {q}")
    print('='*80)
    for desc, model_cfg in [
        ("WITHOUT rerank, top_k=10", {"search_method": "semantic_search", "reranking_enable": False, "top_k": 10, "score_threshold_enabled": False}),
        ("WITH rerank=qwen3-rerank, top_k=10", {"search_method": "semantic_search", "reranking_enable": True, "reranking_mode": "reranking_model", "reranking_model": {"reranking_provider_name": "langgenius/tongyi/tongyi", "reranking_model_name": "qwen3-rerank"}, "top_k": 10, "score_threshold_enabled": False}),
    ]:
        url = f"{BASE}/datasets/{DATASET}/hit-testing"
        try:
            req = urllib.request.Request(url, data=json.dumps({"query": q, "retrieval_model": model_cfg}).encode(), headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read())
            records = body.get("records", [])
            print(f"\n--- {desc} ---  ({len(records)} records)")
            for i, rec in enumerate(records[:5], 1):
                seg = rec.get("segment", {})
                doc = seg.get("document", {})
                print(f"#{i} score={rec.get('score'):.4f}  doc='{doc.get('name')[:40]}'")
        except urllib.error.HTTPError as e:
            print(f"\n--- {desc} --- ERR {e.code}: {e.read().decode()[:300]}")
        except Exception as e:
            print(f"\n--- {desc} --- ERR: {e}")
PY
