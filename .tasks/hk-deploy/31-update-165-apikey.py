#!/usr/bin/env python3
"""Update tongyi API key on 165 Dify via console API."""
import http.cookiejar as cookielib
import json
import ssl
import base64
import urllib.error
import urllib.request

DIFY = "http://localhost:3000/console/api"
EMAIL = "easten_zero@qq.com"
PASSWORD = "ZhaYeFan05.07.14"
NEW_KEY = "sk-658798075c9a4f1ca62551e09e9c0349"

COOK = cookielib.CookieJar()
opener = urllib.request.build_opener(
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


# 1) login
pass_b64 = base64.b64encode(PASSWORD.encode()).decode()
code, body = req("POST", "/login", body={
    "email": EMAIL,
    "password": pass_b64,
    "language": "zh-Hans",
    "remember_me": True,
})
print(f"login: {code} {str(body)[:100]}")

if code != 200:
    print("Login failed, trying different password...")
    # try INIT password
    for pw in ["hB8UKWNhOquM8UmN", PASSWORD]:
        pw_b64 = base64.b64encode(pw.encode()).decode()
        code, body = req("POST", "/login", body={
            "email": EMAIL, "password": pw_b64,
            "language": "zh-Hans", "remember_me": True,
        })
        print(f"  try pw={pw[:5]}...: {code}")
        if code == 200:
            break

if code != 200:
    print("Cannot login. Exiting.")
    raise SystemExit(1)

# 2) List model providers to find tongyi
code, body = req("GET", "/workspaces/current/model-providers", hdrs=auth())
print(f"\nmodel-providers: {code}")
if code == 200 and isinstance(body, dict):
    data = body.get("data", body)
    if isinstance(data, list):
        for p in data:
            provider = p.get("provider", "")
            if "tongyi" in provider.lower() or "dashscope" in provider.lower():
                print(f"  FOUND: {provider} status={p.get('status')} quota={p.get('quota_type')}")
                # show credentials
                for m in p.get("models", [])[:3]:
                    print(f"    model: {m.get('model')} status={m.get('status')}")

# 3) Update tongyi credentials with new API key
print("\n=== Updating tongyi API key ===")
# Dify 1.13: plugin-based model providers use different endpoint
# Try both old and new-style endpoints
for endpoint in [
    "/workspaces/current/model-providers/tongyi/credentials",
    "/workspaces/current/model-providers/langgenius/tongyi/tongyi/credentials",
]:
    code, body = req("POST", endpoint, body={
        "credentials": {"dashscope_api_key": NEW_KEY}
    }, hdrs=auth())
    print(f"  {endpoint}: {code} {str(body)[:200]}")
    if code in (200, 201):
        print("  SUCCESS!")
        break

# 4) Verify by listing models again
code, body = req("GET", "/workspaces/current/model-providers", hdrs=auth())
if code == 200 and isinstance(body, dict):
    data = body.get("data", body)
    if isinstance(data, list):
        for p in data:
            provider = p.get("provider", "")
            if "tongyi" in provider.lower():
                print(f"\n  Verified: {provider} status={p.get('status')}")
