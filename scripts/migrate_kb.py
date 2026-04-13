#!/usr/bin/env python3
"""
v1 KB → Dify 知识库迁移脚本

用法:
  python scripts/migrate_kb.py \
    --entries-dir ../yixiaoguan/knowledge-base/entries \
    --dataset-id <global-kb-uuid> \
    --api-key <dataset-api-key> \
    --api-url http://localhost:3000/v1 \
    --output migrate_result.csv

支持断点续传: 如果 output CSV 已存在，会跳过已成功的条目。
同时写入 PG kb_entries 表（需要 --db-url 或从 .env 读取）。
"""
import argparse
import asyncio
import csv
import logging
import os
import re
import sys
import time
from pathlib import Path

import httpx
import yaml

# 添加 gateway 路径以便导入 app 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "services" / "gateway"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RATE_LIMIT = 0.5  # 每次请求间隔秒数


def parse_frontmatter(filepath: Path) -> tuple[dict, str]:
    """解析 YAML frontmatter + 正文"""
    text = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.+?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1))
    body = match.group(2).strip()
    return meta or {}, body


async def create_document(client, api_url, dataset_id, api_key, title, content):
    """调 Dify Dataset API 创建文档"""
    resp = await client.post(
        f"{api_url}/datasets/{dataset_id}/document/create-by-text",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "name": title,
            "text": content,
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"},
        },
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()


async def save_kb_entry(db_session, meta, doc_id, dataset_id, filename):
    """将 KB 条目写入 PG kb_entries 表"""
    from app.models.kb_entry import KbEntry
    entry = KbEntry(
        dify_document_id=doc_id,
        dify_dataset_id=dataset_id,
        title=meta.get("title", ""),
        category=meta.get("category"),
        tags=meta.get("tags"),
        original_source=meta.get("source"),
        source_url=meta.get("source_url"),
        material_id=meta.get("material_id"),
        campus=meta.get("campus"),
        original_filename=filename,
    )
    db_session.add(entry)
    await db_session.commit()


async def main():
    parser = argparse.ArgumentParser(description="Migrate KB entries to Dify")
    parser.add_argument("--entries-dir", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--api-url", default="http://localhost:3000/v1")
    parser.add_argument("--output", default="migrate_result.csv")
    parser.add_argument("--no-db", action="store_true", help="Skip PG kb_entries write")
    args = parser.parse_args()

    entries_dir = Path(args.entries_dir)
    output_path = Path(args.output)

    # 初始化 DB session（可选）
    db_session = None
    if not args.no_db:
        try:
            from app.database import async_session
            db_session = async_session()
            logger.info("PG kb_entries 写入已启用")
        except Exception as e:
            logger.warning(f"无法连接 DB，跳过 kb_entries 写入: {e}")
            db_session = None

    # 加载已完成的条目（断点续传）
    done_files = set()
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status") == "ok":
                    done_files.add(row["filename"])
        logger.info(f"已完成 {len(done_files)} 条，跳过")

    # 扫描 KB 文件
    md_files = sorted(entries_dir.glob("KB-*.md"))
    logger.info(f"发现 {len(md_files)} 个 KB 文件，{len(md_files) - len(done_files)} 条待迁移")

    # 打开 CSV（追加模式）
    write_header = not output_path.exists() or os.path.getsize(output_path) == 0
    csv_file = open(output_path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=["filename", "title", "category", "document_id", "status", "error"])
    if write_header:
        writer.writeheader()

    success, fail = 0, 0
    async with httpx.AsyncClient() as client:
        for md_file in md_files:
            if md_file.name in done_files:
                continue

            meta, body = parse_frontmatter(md_file)
            title = meta.get("title", md_file.stem)
            category = meta.get("category", "")

            if not body.strip():
                writer.writerow({"filename": md_file.name, "title": title,
                                 "category": category, "document_id": "",
                                 "status": "skip", "error": "empty body"})
                continue

            try:
                result = await create_document(
                    client, args.api_url, args.dataset_id,
                    args.api_key, title, body,
                )
                doc_id = result.get("document", {}).get("id", "?")
                writer.writerow({"filename": md_file.name, "title": title,
                                 "category": category, "document_id": doc_id,
                                 "status": "ok", "error": ""})
                success += 1
                logger.info(f"[{success}] {title} → {doc_id}")

                # 写入 PG
                if db_session:
                    try:
                        await save_kb_entry(db_session, meta, doc_id, args.dataset_id, md_file.name)
                    except Exception as db_err:
                        logger.warning(f"DB write failed for {md_file.name}: {db_err}")

            except Exception as e:
                writer.writerow({"filename": md_file.name, "title": title,
                                 "category": category, "document_id": "",
                                 "status": "error", "error": str(e)})
                fail += 1
                logger.error(f"FAIL {md_file.name}: {e}")

            csv_file.flush()
            time.sleep(RATE_LIMIT)

    csv_file.close()
    if db_session:
        await db_session.close()
    logger.info(f"迁移完成: {success} 成功, {fail} 失败, {len(done_files)} 跳过")


if __name__ == "__main__":
    asyncio.run(main())
