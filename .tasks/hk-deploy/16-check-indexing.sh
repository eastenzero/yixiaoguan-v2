#!/bin/bash
# Check Dify indexing status for the dataset
DATASET_ID="c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE="http://127.0.0.1:8088/v1"

python3 - <<'PY'
import json, urllib.request
from collections import Counter
DATASET = "c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY = "dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE = "http://127.0.0.1:8088/v1"

c = Counter()
total = 0
for page in range(1, 20):
    url = f"{BASE}/datasets/{DATASET}/documents?page={page}&limit=100"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read())
    except Exception as e:
        print(f"page {page} err: {e}")
        break
    docs = body.get("data", [])
    total = body.get("total", total)
    for d in docs:
        c[d.get("indexing_status")] += 1
    if not body.get("has_more"):
        break
print(f"dataset_total={total}  parsed={sum(c.values())}")
print(f"indexing_status distribution: {dict(c)}")
PY
