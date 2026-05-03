#!/usr/bin/env python3
"""Login to Dify console and create a dataset-level API key for the existing dataset.

Tries multiple known endpoints since Dify versions vary:
  POST /console/api/datasets/api-keys              (1.13 style, body: {})
  POST /console/api/datasets/{dataset_id}/api-keys (older style)

Prints the dataset-... token if successful.
"""
from __future__ import annotations

import http.cookiejar as cookielib
import json
import ssl
import urllib.error
import urllib.request

DIFY_BASE = "https://dify.130814.xyz/console/api"
EMAIL = "easten_zero@qq.com"
PASS_B64 = "WmhhWWVGYW4wNS4wNy4xNA=="
DATASET_ID = "c2363fef-405b-48ab-a0e2-9274a4186cef"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
COOK = cookielib.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(COOK),
)


def cookie_value(name: str) -> str | None:
    for c in COOK:
        if c.name == name:
            return c.value
    return None


def request(method: str, path: str, *, json_body=None, headers=None):
    url = DIFY_BASE + path
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with opener.open(req, timeout=30) as r:
            body = r.read().decode("utf-8")
            try:
                return r.status, json.loads(body)
            except Exception:
                return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body


def auth_headers():
    return {
        "Authorization": f"Bearer {cookie_value('access_token') or ''}",
        "X-Csrf-Token": cookie_value("csrf_token") or "",
    }


def login():
    code, body = request(
        "POST",
        "/login",
        json_body={
            "email": EMAIL,
            "password": PASS_B64,
            "language": "zh-Hans",
            "remember_me": True,
        },
    )
    print(f"[login] {code} {body}")
    if code != 200:
        raise SystemExit("login failed")


def list_existing_keys():
    paths = [
        "/datasets/api-keys",
        f"/datasets/{DATASET_ID}/api-keys",
    ]
    for p in paths:
        code, body = request("GET", p, headers=auth_headers())
        print(f"[GET {p}] {code} {body}")


def try_create():
    paths = [
        ("/datasets/api-keys", {}),
        (f"/datasets/{DATASET_ID}/api-keys", {}),
    ]
    for p, payload in paths:
        code, body = request("POST", p, json_body=payload, headers=auth_headers())
        print(f"[POST {p}] {code} {body}")
        if code in (200, 201) and isinstance(body, dict):
            for k in ("token", "secret_key", "api_key", "key"):
                if k in body:
                    print()
                    print("=" * 60)
                    print(f"DATASET API KEY = {body[k]}")
                    print("=" * 60)
                    return body[k]
            # nested?
            if "data" in body and isinstance(body["data"], dict):
                d = body["data"]
                for k in ("token", "secret_key", "api_key", "key"):
                    if k in d:
                        print()
                        print("=" * 60)
                        print(f"DATASET API KEY = {d[k]}")
                        print("=" * 60)
                        return d[k]
    return None


def main():
    login()
    print("\n--- list existing dataset keys ---")
    list_existing_keys()
    print("\n--- create dataset key ---")
    key = try_create()
    if not key:
        print("\n!! could not auto-create. Try Dify UI: 知识库 → 设置 → API 访问 → 创建密钥")


if __name__ == "__main__":
    main()
