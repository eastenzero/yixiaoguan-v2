#!/usr/bin/env python3
"""Dify 1.13 console: import chatflow DSL and create API key.

Steps:
  1. login (email + base64 password) -> save cookies, extract access_token + csrf_token
  2. POST /console/api/apps/imports {mode: 'yaml-content', yaml_content: <full yaml>}
     -> get back {id (import id), app_id, status}
  3. confirm app exists (GET /console/api/apps?page=1&limit=10) and grab its id
  4. POST /console/api/apps/<app_id>/api-keys -> get secret_key (app-...)
  5. Print summary so caller can inject into gateway .env
"""
from __future__ import annotations

import http.cookiejar as cookielib
import json
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DIFY_BASE = "https://dify.130814.xyz/console/api"
EMAIL = "easten_zero@qq.com"
PASS_B64 = "WmhhWWVGYW4wNS4wNy4xNA=="  # base64('ZhaYeFan05.07.14')
DSL_PATH = "/tmp/chatflow_v2_d1.yaml"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

COOK = cookielib.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=CTX),
    urllib.request.HTTPCookieProcessor(COOK),
)


def request(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    headers: dict | None = None,
):
    url = DIFY_BASE + path
    data = None
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with opener.open(req, timeout=30) as r:
            body = r.read().decode("utf-8")
            try:
                return r.status, json.loads(body)
            except json.JSONDecodeError:
                return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def cookie_value(name: str) -> str | None:
    for c in COOK:
        if c.name == name:
            return c.value
    return None


def auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {cookie_value('access_token') or ''}",
        "X-Csrf-Token": cookie_value("csrf_token") or "",
    }


def login() -> None:
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
    if code != 200:
        raise SystemExit(f"login failed [{code}]: {body}")
    print(f"[login] {body}")


def import_dsl(yaml_text: str) -> dict:
    code, body = request(
        "POST",
        "/apps/imports",
        json_body={"mode": "yaml-content", "yaml_content": yaml_text},
        headers=auth_headers(),
    )
    print(f"[import] http={code} body={body}")
    if code not in (200, 201):
        raise SystemExit(f"import failed: {body}")
    return body


def list_apps() -> list:
    code, body = request("GET", "/apps?page=1&limit=20", headers=auth_headers())
    if code != 200 or not isinstance(body, dict):
        raise SystemExit(f"list apps failed: {body}")
    return body.get("data", [])


def create_api_key(app_id: str) -> dict:
    code, body = request(
        "POST",
        f"/apps/{app_id}/api-keys",
        json_body={},
        headers=auth_headers(),
    )
    print(f"[api-key] http={code} body={body}")
    if code not in (200, 201):
        raise SystemExit(f"create key failed: {body}")
    return body


def main() -> None:
    yaml_text = Path(DSL_PATH).read_text(encoding="utf-8")
    print(f"DSL bytes={len(yaml_text)}")

    login()

    imported = import_dsl(yaml_text)
    app_id = imported.get("app_id") or imported.get("appId")

    if not app_id:
        print("[warn] import response has no app_id, scanning /apps for newest")
        apps = list_apps()
        if apps:
            app_id = apps[0].get("id")
        else:
            raise SystemExit("no apps after import")

    print(f"app_id={app_id}")

    apps = list_apps()
    print(f"apps in workspace: {len(apps)}")
    for a in apps:
        print(f"  - {a.get('id')} | {a.get('name')} | mode={a.get('mode')}")

    key = create_api_key(app_id)
    secret = key.get("token") or key.get("api_key") or key.get("secret_key")
    print()
    print("=" * 60)
    print(f"APP_ID    = {app_id}")
    print(f"API_KEY   = {secret}")
    print("=" * 60)


if __name__ == "__main__":
    main()
