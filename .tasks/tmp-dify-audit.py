#!/usr/bin/env python3
"""Audit HK Dify datasets and retrieval config."""
import urllib.request
import urllib.parse
import json
import ssl

BASE = "http://127.0.0.1:8088"
TARGET_DS = "c2363fef-405b-48ab-a0e2-9274a4186cef"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ALL_COOKIES = {}

def api(method, path, data=None, token=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # Send all cookies
    if ALL_COOKIES:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in ALL_COOKIES.items())
    # CSRF token from cookies
    if "csrf_token" in ALL_COOKIES:
        headers["X-Csrf-Token"] = ALL_COOKIES["csrf_token"]
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode()
        # Parse Set-Cookie headers
        for h in resp.headers.get_all("Set-Cookie") or []:
            parts = h.split(";")[0].split("=", 1)
            if len(parts) == 2:
                ALL_COOKIES[parts[0].strip()] = parts[1].strip()
        return json.loads(raw), resp.getcode()
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return json.loads(raw) if raw else {}, e.code

# Step 1: Login
print("=== LOGIN ===")
login_data = {
    "email": "easten_zero@qq.com",
    "password": "WmhhWWVGYW4wNS4wNy4xNA==",
    "language": "zh-Hans",
    "remember_me": True
}
resp, code = api("POST", "/console/api/login", login_data)
print(f"Status: {code}, Response: {json.dumps(resp)[:200]}")
print(f"Cookies collected: {list(ALL_COOKIES.keys())}")

token = None
if "data" in resp and isinstance(resp["data"], dict):
    token = resp["data"].get("access_token")
elif "access_token" in resp:
    token = resp["access_token"]

# Also check cookie for access_token
if not token and "access_token" in ALL_COOKIES:
    token = ALL_COOKIES["access_token"]
    print(f"Using cookie-based token: {token[:20]}...")

if token:
    print(f"Token: {token[:20]}...")

# Step 2: List datasets
print("\n=== ALL DATASETS ===")
headers_extra = {}
ds_resp, ds_code = api("GET", "/console/api/datasets?page=1&limit=20", token=token)
print(f"Status: {ds_code}")

if "data" in ds_resp:
    for ds in ds_resp["data"]:
        print(f"\nDataset: {ds.get('name', '?')}")
        print(f"  ID: {ds['id']}")
        print(f"  Documents: {ds.get('document_count', '?')}")
        print(f"  Embedding Model: {ds.get('embedding_model', '?')}")
        print(f"  Embedding Provider: {ds.get('embedding_model_provider', '?')}")
        rm = ds.get("retrieval_model_dict") or ds.get("retrieval_model") or {}
        if rm:
            print(f"  Retrieval Config: {json.dumps(rm, indent=4)}")
        is_target = "*** THIS IS GATEWAY TARGET ***" if ds["id"] == TARGET_DS else ""
        if is_target:
            print(f"  {is_target}")
elif "code" in ds_resp:
    print(f"Error: {ds_resp}")
else:
    print(f"Raw: {json.dumps(ds_resp)[:500]}")

# Step 3: Check target dataset specifically
print(f"\n=== TARGET DATASET: {TARGET_DS} ===")
tgt_resp, tgt_code = api("GET", f"/console/api/datasets/{TARGET_DS}", token=token)
print(f"Status: {tgt_code}")
if tgt_code == 200:
    print(f"Name: {tgt_resp.get('name', '?')}")
    print(f"Doc Count: {tgt_resp.get('document_count', '?')}")
    print(f"Word Count: {tgt_resp.get('word_count', '?')}")
    print(f"Embedding Model: {tgt_resp.get('embedding_model', '?')}")
    print(f"Embedding Provider: {tgt_resp.get('embedding_model_provider', '?')}")
    print(f"Indexing Tech: {tgt_resp.get('indexing_technique', '?')}")
    rm = tgt_resp.get("retrieval_model_dict") or tgt_resp.get("retrieval_model") or {}
    print(f"Retrieval Config: {json.dumps(rm, indent=2)}")
else:
    print(f"Response: {json.dumps(tgt_resp)[:300]}")

# Step 4: List documents in target dataset (first 10)
print(f"\n=== DOCUMENTS IN TARGET (first 10) ===")
doc_resp, doc_code = api("GET", f"/console/api/datasets/{TARGET_DS}/documents?page=1&limit=10", token=token)
if doc_code == 200 and "data" in doc_resp:
    print(f"Total documents: {doc_resp.get('total', '?')}")
    for doc in doc_resp["data"][:10]:
        print(f"  - {doc.get('name', '?')} (tokens: {doc.get('tokens', '?')}, segments: {doc.get('segment_count', doc.get('completed_segments', '?'))})")
else:
    print(f"Status {doc_code}: {json.dumps(doc_resp)[:300]}")
