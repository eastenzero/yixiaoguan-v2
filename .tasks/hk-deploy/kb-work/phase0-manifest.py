#!/usr/bin/env python3
"""Phase 0 — Generate manifest.csv for all 1267 KB entries.

Each row: source(v1|v2), filename, doc_id_or_legacy, title, category, tags(joined), status, body_chars, body_preview(200chars), source_field
"""
from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
SRC_V1 = ROOT / "src-v1"
SRC_V2 = ROOT / "src-v2"
OUT = ROOT / "manifest.csv"

FRONT_RE = re.compile(r"^---\n(.+?)\n---\n(.*)$", re.DOTALL)


def parse(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONT_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1))
    except Exception:
        meta = {}
    body = m.group(2).strip()
    return meta or {}, body


def collect(src: Path, source_label: str):
    rows = []
    for p in sorted(src.glob("*.md")):
        meta, body = parse(p)
        title = str(meta.get("title", "")).strip()
        category = str(meta.get("category", "")).strip()

        # tags can be list or string
        tags_field = meta.get("tags") or []
        if isinstance(tags_field, str):
            tags = [tags_field]
        elif isinstance(tags_field, list):
            tags = [str(t) for t in tags_field]
        else:
            tags = []

        # doc_id (v2) or material_id (v1) or filename stem
        doc_id = str(meta.get("doc_id") or meta.get("material_id") or p.stem).strip()

        status = str(meta.get("status", "")).strip() or ("published" if source_label == "v2" else "")

        # source field for v1 (page ref) or sources array for v2
        if "sources" in meta and isinstance(meta["sources"], list):
            src_field = " | ".join(
                f"{s.get('type','?')}:{s.get('path','?')}" for s in meta["sources"]
            )
        elif "source" in meta:
            src_field = str(meta.get("source", ""))
        else:
            src_field = ""

        rows.append(
            {
                "source": source_label,
                "filename": p.name,
                "doc_id": doc_id,
                "title": title,
                "category": category,
                "tags": "|".join(tags),
                "status": status,
                "body_chars": len(body),
                "body_preview": body[:200].replace("\n", " "),
                "source_field": src_field[:300],
            }
        )
    return rows


def main():
    rows = []
    rows += collect(SRC_V1, "v1")
    rows += collect(SRC_V2, "v2")

    fieldnames = [
        "source",
        "filename",
        "doc_id",
        "title",
        "category",
        "tags",
        "status",
        "body_chars",
        "body_preview",
        "source_field",
    ]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # summary
    from collections import Counter
    src_count = Counter(r["source"] for r in rows)
    cat_v1 = Counter(r["category"] for r in rows if r["source"] == "v1")
    cat_v2 = Counter(r["category"] for r in rows if r["source"] == "v2")
    status_v1 = Counter(r["status"] for r in rows if r["source"] == "v1")
    body_avg_v1 = sum(r["body_chars"] for r in rows if r["source"] == "v1") / max(1, src_count["v1"])
    body_avg_v2 = sum(r["body_chars"] for r in rows if r["source"] == "v2") / max(1, src_count["v2"])

    print(f"manifest.csv  total={len(rows)}  v1={src_count['v1']}  v2={src_count['v2']}")
    print(f"\nv1 categories ({len(cat_v1)} unique):")
    for c, n in cat_v1.most_common():
        print(f"  {c!r}: {n}")
    print(f"\nv2 categories ({len(cat_v2)} unique):")
    for c, n in cat_v2.most_common():
        print(f"  {c!r}: {n}")
    print(f"\nv1 status distribution: {dict(status_v1)}")
    print(f"\navg body chars  v1={body_avg_v1:.0f}  v2={body_avg_v2:.0f}")


if __name__ == "__main__":
    main()
