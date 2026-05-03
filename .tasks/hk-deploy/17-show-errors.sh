#!/bin/bash
python3 - <<'PY'
import json, urllib.request
DATASET = "c2363fef-405b-48ab-a0e2-9274a4186cef"
KEY = "dataset-Cw9zcTBywGSgBAlivhRrKn6k"
BASE = "http://127.0.0.1:8088/v1"

errors = []
waiting = []
indexing = []
completed = 0
for page in range(1, 7):
    url = f"{BASE}/datasets/{DATASET}/documents?page={page}&limit=100"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        body = json.loads(r.read())
    docs = body.get("data", [])
    for d in docs:
        st = d.get("indexing_status")
        if st == "error":
            errors.append(d)
        elif st == "waiting":
            waiting.append(d)
        elif st == "indexing":
            indexing.append(d)
        elif st == "completed":
            completed += 1
    if not body.get("has_more"):
        break

print(f"completed={completed}  indexing={len(indexing)}  waiting={len(waiting)}  error={len(errors)}")
print()
print("=== first 5 errors ===")
for d in errors[:5]:
    print(f"name='{d.get('name')}'  err='{d.get('error')}'  word_count={d.get('word_count')}")
PY
