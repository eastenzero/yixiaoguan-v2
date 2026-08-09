#!/usr/bin/env python3
"""Export Dify Weaviate object metadata as JSON Lines.

This script is deliberately read-only. It uses only the Weaviate REST API and
does not invoke Dify's Dataset or Chat APIs, so running it cannot create query
logs or mutate a knowledge base.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request


def fetch_json(url: str, api_key: str | None = None) -> dict:
    request = urllib.request.Request(url)  # noqa: S310 - trusted internal endpoint
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - trusted internal endpoint
        return json.load(response)


def main() -> int:
    endpoint = os.environ.get("WEAVIATE_ENDPOINT", "http://weaviate:8080").rstrip("/")
    api_key = os.environ.get("WEAVIATE_API_KEY") or None
    schema = fetch_json(f"{endpoint}/v1/schema", api_key)
    collections = sorted(
        item["class"]
        for item in schema.get("classes", [])
        if item.get("class", "").startswith("Vector_index_")
    )

    page_size = 100
    for collection in collections:
        after: str | None = None
        exported = 0
        while True:
            params = {"class": collection, "limit": str(page_size)}
            if after:
                params["after"] = after
            url = f"{endpoint}/v1/objects?{urllib.parse.urlencode(params)}"
            page = fetch_json(url, api_key)
            objects = page.get("objects") or []
            for obj in objects:
                row = {
                    "collection": collection,
                    "object_id": obj.get("id"),
                    "properties": obj.get("properties") or {},
                }
                print(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            exported += len(objects)
            if len(objects) < page_size:
                break
            after = objects[-1]["id"]
        print(f"exported {collection}: {exported}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
