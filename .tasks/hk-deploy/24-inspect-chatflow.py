#!/usr/bin/env python3
"""Inspect knowledge_retrieval node config in the published chatflow."""
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
        if c.name == name:
            return c.value
    return None


def req(method, path, *, body=None, hdrs=None):
    url = DIFY + path
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if hdrs:
        h.update(hdrs)
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


# login
code, body = req(
    "POST", "/login",
    body={"email": EMAIL, "password": PASS_B64, "language": "zh-Hans", "remember_me": True}
)
print(f"login: {code}")

# get published workflow
for endpoint in [
    f"/apps/{APP_ID}/workflows/publish",
    f"/apps/{APP_ID}/workflows/draft",
]:
    code, body = req("GET", endpoint, hdrs=auth())
    print(f"\n=== {endpoint} : {code} ===")
    if code == 200 and isinstance(body, dict):
        graph = body.get("graph", {})
        nodes = graph.get("nodes", [])
        for n in nodes:
            data = n.get("data", {})
            ntype = data.get("type")
            title = data.get("title")
            if ntype in ("knowledge-retrieval", "llm"):
                print(f"\n--- {ntype} :: {title} ---")
                if ntype == "knowledge-retrieval":
                    keys = ["dataset_ids", "retrieval_mode", "multiple_retrieval_config", "single_retrieval_config", "query_variable_selector"]
                    for k in keys:
                        if k in data:
                            print(f"  {k}: {json.dumps(data[k], ensure_ascii=False)}")
                elif ntype == "llm":
                    keys = ["context", "model", "prompt_template"]
                    for k in keys:
                        if k in data:
                            v = data[k]
                            if isinstance(v, list) and v:
                                v = v[0] if isinstance(v[0], dict) else v
                            print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
