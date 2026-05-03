#!/usr/bin/env python3
"""Fix HK Dify dataset: update retrieval config + identify junk docs."""
import urllib.request
import json
import sys

BASE = "http://127.0.0.1:8088"
TARGET_DS = "c2363fef-405b-48ab-a0e2-9274a4186cef"

ALL_COOKIES = {}

def api(method, path, data=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if ALL_COOKIES:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in ALL_COOKIES.items())
    if "csrf_token" in ALL_COOKIES:
        headers["X-Csrf-Token"] = ALL_COOKIES["csrf_token"]
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read().decode()
        for h in resp.headers.get_all("Set-Cookie") or []:
            parts = h.split(";")[0].split("=", 1)
            if len(parts) == 2:
                ALL_COOKIES[parts[0].strip()] = parts[1].strip()
        return json.loads(raw) if raw.strip() else {}, resp.getcode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return json.loads(raw), e.code
        except:
            return {"error": raw}, e.code

# === Step 0: Login ===
print("=" * 60)
print("STEP 0: Login")
print("=" * 60)
resp, code = api("POST", "/console/api/login", {
    "email": "easten_zero@qq.com",
    "password": "WmhhWWVGYW4wNS4wNy4xNA==",
    "language": "zh-Hans",
    "remember_me": True
})
if code != 200 or resp.get("result") != "success":
    print(f"LOGIN FAILED: {code} {resp}")
    sys.exit(1)
print(f"Login OK. Cookies: {list(ALL_COOKIES.keys())}")

# === Step 1: Update retrieval config ===
print()
print("=" * 60)
print("STEP 1: Update retrieval config")
print("  - rerank: qwen3-rerank -> gte-rerank-v2")
print("  - top_k: 4 -> 5")
print("=" * 60)

new_retrieval = {
    "search_method": "semantic_search",
    "reranking_enable": True,
    "reranking_mode": "reranking_model",
    "reranking_model": {
        "reranking_provider_name": "langgenius/tongyi/tongyi",
        "reranking_model_name": "gte-rerank-v2"
    },
    "weights": {
        "weight_type": "customized",
        "keyword_setting": {
            "keyword_weight": 0.3
        },
        "vector_setting": {
            "vector_weight": 0.7,
            "embedding_model_name": "text-embedding-v4",
            "embedding_provider_name": "langgenius/tongyi/tongyi"
        }
    },
    "top_k": 5,
    "score_threshold_enabled": False,
    "score_threshold": 0.0
}

# Dify console API: PATCH /console/api/datasets/{id}
# But retrieval_model might need to be set differently. Let's try PUT on the settings endpoint
# Actually for Dify 1.13.x, we update via PUT /console/api/datasets/{id}
update_resp, update_code = api("PATCH", f"/console/api/datasets/{TARGET_DS}", {
    "retrieval_model": new_retrieval
})
if update_code == 200:
    # Verify
    verify, _ = api("GET", f"/console/api/datasets/{TARGET_DS}")
    rm = verify.get("retrieval_model_dict") or verify.get("retrieval_model") or {}
    rerank_name = "?"
    top_k = "?"
    if isinstance(rm, dict):
        rr = rm.get("reranking_model", {})
        rerank_name = rr.get("reranking_model_name", "?")
        top_k = rm.get("top_k", "?")
    print(f"UPDATE OK!")
    print(f"  Rerank model now: {rerank_name}")
    print(f"  Top-K now: {top_k}")
else:
    print(f"UPDATE FAILED: {update_code}")
    print(f"Response: {json.dumps(update_resp)[:500]}")
    # Try alternative field name
    print("Trying alternative: retrieval_model_dict...")
    update_resp2, update_code2 = api("PATCH", f"/console/api/datasets/{TARGET_DS}", {
        "retrieval_model_dict": new_retrieval
    })
    if update_code2 == 200:
        print("UPDATE OK (via retrieval_model_dict)!")
    else:
        print(f"Also failed: {update_code2} {json.dumps(update_resp2)[:300]}")

# === Step 2: Identify junk documents ===
print()
print("=" * 60)
print("STEP 2: Scan for non-KB junk documents")
print("=" * 60)

junk_docs = []
page = 1
total_docs = 0
while True:
    docs_resp, docs_code = api("GET", f"/console/api/datasets/{TARGET_DS}/documents?page={page}&limit=100")
    if docs_code != 200:
        print(f"Error fetching page {page}: {docs_code}")
        break
    data = docs_resp.get("data", [])
    total = docs_resp.get("total", 0)
    if not data:
        break
    total_docs += len(data)
    for doc in data:
        name = doc.get("name", "")
        tokens = doc.get("tokens", 0) or 0
        doc_id = doc.get("id", "")
        # Junk criteria: very short name AND very few tokens (likely test input)
        # Real KB entries have names like "XXX学院 — XXX" or "XX部 — XX指南"
        is_junk = False
        reason = ""
        if tokens < 150 and len(name) < 15:
            is_junk = True
            reason = f"too short (tokens={tokens}, name_len={len(name)})"
        if name in ["你好", "我想转人工服务", "测试", "test", "hello"]:
            is_junk = True
            reason = f"test content: '{name}'"
        if is_junk:
            junk_docs.append({"id": doc_id, "name": name, "tokens": tokens, "reason": reason})
    if total_docs >= total:
        break
    page += 1

print(f"Total documents scanned: {total_docs}")
print(f"Junk documents found: {len(junk_docs)}")
for j in junk_docs:
    print(f"  JUNK: '{j['name']}' (tokens={j['tokens']}, reason={j['reason']}, id={j['id']})")

# === Step 3: Delete junk documents ===
if junk_docs:
    print()
    print("=" * 60)
    print(f"STEP 3: Deleting {len(junk_docs)} junk documents")
    print("=" * 60)
    deleted = 0
    failed = 0
    for j in junk_docs:
        del_resp, del_code = api("DELETE", f"/console/api/datasets/{TARGET_DS}/documents/{j['id']}")
        if del_code == 200 or del_code == 204:
            print(f"  DELETED: '{j['name']}'")
            deleted += 1
        else:
            print(f"  FAILED: '{j['name']}' -> {del_code} {json.dumps(del_resp)[:100]}")
            failed += 1
    print(f"\nDeleted: {deleted}, Failed: {failed}")
else:
    print("\nNo junk documents to delete.")

# === Final verification ===
print()
print("=" * 60)
print("FINAL VERIFICATION")
print("=" * 60)
final_resp, final_code = api("GET", f"/console/api/datasets/{TARGET_DS}")
if final_code == 200:
    print(f"Dataset: {final_resp.get('name', '?')}")
    print(f"Doc Count: {final_resp.get('document_count', '?')}")
    print(f"Embedding Model: {final_resp.get('embedding_model', '?')}")
    rm = final_resp.get("retrieval_model_dict") or final_resp.get("retrieval_model") or {}
    if isinstance(rm, dict):
        rr = rm.get("reranking_model", {})
        print(f"Rerank Model: {rr.get('reranking_model_name', '?')}")
        print(f"Top-K: {rm.get('top_k', '?')}")
    print(f"Word Count: {final_resp.get('word_count', '?')}")
print("\nDone!")
