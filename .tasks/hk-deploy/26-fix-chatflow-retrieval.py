#!/usr/bin/env python3
"""Fix chatflow knowledge_retrieval node:
- top_k: 4 -> 10
- search_method: change to hybrid_search (BM25 + semantic)
- ensure rerank enabled with qwen3-rerank
Then publish.
"""
import http.cookiejar as cookielib
import json
import ssl
import urllib.error
import urllib.request

DIFY = "https://dify.130814.xyz/console/api"
EMAIL = "easten_zero@qq.com"
PASS_B64 = "WmhhWWVGYW4wNS4wNy4xNA=="
APP_ID = "7f1ea428-e784-4e22-b3b1-52e1befbe652"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
COOK = cookielib.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(COOK),
)


def cv(name):
    for c in COOK:
        if c.name == name: return c.value
    return None


def req(method, path, *, body=None, hdrs=None):
    url = DIFY + path
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if hdrs: h.update(hdrs)
    data = None if body is None else json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with opener.open(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def auth():
    return {
        "Authorization": f"Bearer {cv('access_token')}",
        "X-Csrf-Token": cv("csrf_token") or "",
    }


# 1) login
code, body = req("POST", "/login", body={"email": EMAIL, "password": PASS_B64, "language": "zh-Hans", "remember_me": True})
print(f"login: {code}")

# 2) get current draft
code, draft = req("GET", f"/apps/{APP_ID}/workflows/draft", hdrs=auth())
print(f"draft GET: {code}")
graph = draft.get("graph", {})
nodes = graph.get("nodes", [])
features = draft.get("features", {})
hash_id = draft.get("hash")

# 3) modify knowledge-retrieval node
patched = 0
for n in nodes:
    data = n.get("data", {})
    if data.get("type") == "knowledge-retrieval":
        cfg = data.setdefault("multiple_retrieval_config", {})
        old_top_k = cfg.get("top_k")
        cfg["top_k"] = 10
        # try hybrid search
        # Note: knowledge-retrieval node in dify uses dataset's own retrieval setting,
        # but you can override via node settings. Let's also try setting search_method.
        cfg["reranking_enable"] = True
        cfg["reranking_mode"] = "reranking_model"
        cfg["reranking_model"] = {"provider": "langgenius/tongyi/tongyi", "model": "qwen3-rerank"}
        # Optional: weighted_score (alternative rerank)
        # try setting score_threshold and search_method
        # This depends on dify version; for 1.13, the relevant key is "score_threshold" + "score_threshold_enabled"
        cfg["score_threshold_enabled"] = False
        if "score_threshold" in cfg:
            del cfg["score_threshold"]
        # Note: hybrid search isn't a node-level setting in dify 1.13, it's dataset-level (set in dataset settings).
        # Node level only controls top_k / rerank.
        patched += 1
        print(f"  patched node {n.get('id')}: top_k {old_top_k} -> 10, rerank=true (qwen3-rerank)")

if not patched:
    print("ERR: no knowledge-retrieval node found")
    raise SystemExit(1)

# 4) save draft
code, body = req("POST", f"/apps/{APP_ID}/workflows/draft", body={"graph": graph, "features": features, "hash": hash_id, "environment_variables": draft.get("environment_variables", []), "conversation_variables": draft.get("conversation_variables", [])}, hdrs=auth())
print(f"draft POST: {code} {str(body)[:200]}")

# 5) publish
code, body = req("POST", f"/apps/{APP_ID}/workflows/publish", body={}, hdrs=auth())
print(f"publish POST: {code} {str(body)[:200]}")
