#!/usr/bin/env python3
"""Retry indexing for documents in `error` state (DashScope 429 rate limit).

Steps:
  1. login Dify console
  2. list all docs in dataset, collect those with indexing_status=='error'
  3. POST /console/api/datasets/{dataset_id}/retry  body: {"document_ids": [...]}
  4. poll until all retried docs flip to completed (or hit 5min ceiling)
"""
from __future__ import annotations

import http.cookiejar as cookielib
import json
import ssl
import time
import urllib.error
import urllib.request
from collections import Counter

DIFY = "https://dify.130814.xyz/console/api"
EMAIL = "easten_zero@qq.com"
PASS_B64 = "WmhhWWVGYW4wNS4wNy4xNA=="
DATASET = "c2363fef-405b-48ab-a0e2-9274a4186cef"
DATASET_KEY = "dataset-Cw9zcTBywGSgBAlivhRrKn6k"

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


def req(method, path, *, body=None, base=DIFY, hdrs=None):
    url = base + path
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if hdrs:
        h.update(hdrs)
    data = None if body is None else json.dumps(body).encode("utf-8")
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with opener.open(r, timeout=30) as resp:
            txt = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(txt)
            except Exception:
                return resp.status, txt
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, txt


def auth():
    return {
        "Authorization": f"Bearer {cv('access_token')}",
        "X-Csrf-Token": cv("csrf_token") or "",
    }


def login():
    code, body = req(
        "POST",
        "/login",
        body={"email": EMAIL, "password": PASS_B64, "language": "zh-Hans", "remember_me": True},
    )
    if code != 200:
        raise SystemExit(f"login failed: {code} {body}")
    print(f"[login] {body}")


def list_docs():
    """Use dataset API key (simpler) for listing."""
    docs = []
    for page in range(1, 7):
        url = f"http://127.0.0.1:8088/v1/datasets/{DATASET}/documents?page={page}&limit=100"
        # service api uses dataset key
        r = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {DATASET_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(r, timeout=20) as resp:
            body = json.loads(resp.read())
        docs.extend(body.get("data", []))
        if not body.get("has_more"):
            break
    return docs


def main():
    login()
    docs = list_docs()
    c = Counter(d.get("indexing_status") for d in docs)
    print(f"current: total={len(docs)} dist={dict(c)}")

    waiting_or_indexing = [d for d in docs if d.get("indexing_status") in ("waiting", "indexing", "parsing")]
    errors = [d for d in docs if d.get("indexing_status") == "error"]

    if waiting_or_indexing:
        print(f"[!] {len(waiting_or_indexing)} docs still waiting/indexing, polling 60s...")
        for _ in range(12):
            time.sleep(5)
            docs2 = list_docs()
            c2 = Counter(d.get("indexing_status") for d in docs2)
            print(f"  poll: {dict(c2)}")
            if not any(d.get("indexing_status") in ("waiting", "indexing", "parsing") for d in docs2):
                docs = docs2
                errors = [d for d in docs if d.get("indexing_status") == "error"]
                break
        else:
            print("[!] still in flight after 60s; proceed with retry anyway")
            docs = list_docs()
            errors = [d for d in docs if d.get("indexing_status") == "error"]

    if not errors:
        print("\nNo errors to retry. All done.")
        return

    print(f"\n[retry] sending retry for {len(errors)} error docs")
    ids = [d["id"] for d in errors]
    print(f"first 3 ids: {ids[:3]}")
    code, body = req("POST", f"/datasets/{DATASET}/retry", body={"document_ids": ids}, hdrs=auth())
    print(f"[retry POST] {code} {body}")

    if code not in (200, 204):
        raise SystemExit("retry call failed")

    # Poll up to 5 min for all to flip to completed
    print("\n[poll] waiting for retried docs to complete (up to 5 min)...")
    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(15)
        docs = list_docs()
        c = Counter(d.get("indexing_status") for d in docs)
        print(f"  poll: {dict(c)}")
        if c.get("error", 0) == 0 and c.get("waiting", 0) == 0 and c.get("indexing", 0) == 0 and c.get("parsing", 0) == 0:
            print("\n[done] all completed!")
            return
    print("\n[timeout] polling deadline reached; check final state above.")


if __name__ == "__main__":
    main()
