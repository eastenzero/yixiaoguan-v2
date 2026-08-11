#!/usr/bin/env python3
"""将校园候选资料整理为可治理的知识卡目录。

仅使用 Python 标准库；不发布、不调用 Dify，不改动生产数据集。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


TOPIC_RULES = [
    ("awards_and_aid", ("奖学金", "助学金", "资助", "助学贷款", "困难认定", "勤工助学", "奖助", "荣誉称号")),
    ("party_and_honors", ("入党", "党员", "党支部", "积极分子", "发展对象", "团员", "推优", "评优", "优秀学生", "优秀干部")),
    ("academic_affairs", ("补考", "重修", "挂科", "成绩", "考试", "缓考", "选课", "学籍", "转专业", "学位", "毕业", "推免")),
    ("campus_life", ("图书馆", "开馆", "闭馆", "借阅", "宿舍", "公寓", "水电", "电费", "食堂", "校园卡", "班车", "场馆")),
    ("digital_services", ("校园邮箱", "校园网", "vpn", "统一身份认证", "信息门户", "密码", "网络中心", "办事大厅")),
    ("employment_and_career", ("就业", "招聘", "宣讲会", "三方协议", "派遣", "毕业生", "职业规划", "创新创业")),
    ("postgraduate", ("研究生", "导师", "中期考核", "培养方案", "学位论文", "学术规范")),
    ("health_and_safety", ("心理", "医保", "校医院", "体检", "保卫", "安全", "实验室")),
    ("finance_and_services", ("学费", "缴费", "报销", "发票", "证明", "印章", "场地申请")),
    ("admissions_and_international", ("招生", "录取", "留学生", "国际交流", "交换生", "出国")),
]

SUBTOPIC_RULES = {
    "awards_and_aid": ("国家奖学金", "国家励志奖学金", "省政府奖学金", "助学金", "困难认定", "助学贷款", "勤工助学", "服兵役资助"),
    "party_and_honors": ("入党申请", "积极分子", "发展对象", "预备党员", "团员推优", "评奖评优", "挂科影响"),
    "academic_affairs": ("选课", "考试", "缓考", "补考", "重修", "成绩复核", "学籍异动", "转专业", "毕业", "学位", "推免"),
    "campus_life": ("图书馆", "宿舍", "水电", "食堂", "校园卡", "班车", "场馆"),
    "digital_services": ("校园邮箱", "校园网", "VPN", "统一身份认证", "办事大厅", "账号与密码"),
}

LEGACY_TOPIC_MAP = {
    "awards": "awards_and_aid",
    "party": "party_and_honors",
    "progression": "academic_affairs",
    "academic_status": "academic_affairs",
    "employment": "employment_and_career",
    "campus_life": "campus_life",
}


def norm_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def clean_title(value: object) -> str:
    title = norm_text(value).lstrip("﻿ ")
    for separator in (" 各学院", " 根据", " 为了", " 为进一步", " 经研究", " 一、"):
        end = title.find(separator)
        if 8 <= end <= 140:
            return title[:end].strip(" -")
    for marker in ("实施细则", "工作方案", "管理办法", "评选办法", "的通知", "的公示", "的公告", "通知", "公示", "公告"):
        end = title.find(marker)
        if 5 <= end <= 100:
            return title[: end + len(marker)].strip(" -")
    return title[:100].rstrip("，, 。")


def clean_content(raw_title: object, raw_excerpt: object, title: str) -> tuple[str, str]:
    title_text = norm_text(raw_title)
    overflow = title_text[len(title):].lstrip(" -：:") if title_text.startswith(title) else ""
    raw = norm_text(f"{overflow} {norm_text(raw_excerpt)}")
    pollution_markers = ("@media", "display:", "width:", "padding:", "margin:", "box-sizing:", "/*", "_jsq_(")
    pieces = re.split(r"(?<=[。！？；])", raw)
    useful = []
    for piece in pieces:
        compact = piece.strip()
        if not compact or any(marker in compact for marker in pollution_markers):
            continue
        if compact.count("{") + compact.count("}") >= 2:
            continue
        useful.append(compact)
        if sum(len(item) for item in useful) >= 1800:
            break
    content = norm_text(" ".join(useful))[:1800]
    if len(content) < 80:
        quality = "page_chrome_polluted" if any(marker in raw for marker in pollution_markers) else "too_short"
    else:
        quality = "usable_excerpt"
    return content, quality


def topic_for(record: dict) -> str:
    haystack = f"{norm_text(record.get('title'))} {norm_text(record.get('content_excerpt'))[:1200]}".lower()
    scores = [(sum(haystack.count(term.lower()) for term in terms), topic) for topic, terms in TOPIC_RULES]
    best_score, best_topic = max(scores, default=(0, "campus_news"))
    if best_score:
        return best_topic
    for legacy in record.get("matched_topics") or []:
        if legacy in LEGACY_TOPIC_MAP:
            return LEGACY_TOPIC_MAP[legacy]
    return "campus_news"


def subtopics_for(topic: str, text: str) -> list[str]:
    lowered = text.lower()
    matches = [term for term in SUBTOPIC_RULES.get(topic, ()) if term.lower() in lowered]
    if topic == "awards_and_aid" and not matches and "奖学金" in text:
        matches.append("学校与学院奖学金")
    return matches[:5]


def student_scope(text: str) -> list[str]:
    scopes = []
    if "研究生" in text or "硕士" in text or "博士" in text:
        scopes.append("研究生")
    if "本科" in text or "学士" in text:
        scopes.append("本科生")
    if "留学生" in text or "国际学生" in text:
        scopes.append("留学生")
    return scopes or ["未明确"]


def campus_scope(text: str) -> list[str]:
    campuses = []
    for campus in ("济南校区", "泰安校区", "章丘校区"):
        if campus in text:
            campuses.append(campus)
    return campuses or ["未明确"]


def year_from(value: str) -> int | None:
    match = re.search(r"(20\d{2})", value or "")
    return int(match.group(1)) if match else None


def temporal_status(record: dict) -> str:
    published = norm_text(record.get("published_at"))
    year = year_from(published) or year_from(norm_text(record.get("title")))
    if bool(record.get("current_window")) or (year and year >= date.today().year - 1):
        return "current_window"
    if year and year >= date.today().year - 3:
        return "recent_reference"
    if year:
        return "historical_reference"
    return "date_unknown"


def evidence_role(material_type: str) -> str:
    return {
        "formal_policy": "rule_evidence",
        "action_notice": "process_evidence",
        "result_notice": "result_context",
        "news_activity": "background_context",
        "needs_review": "background_context",
    }.get(material_type, "background_context")


def answer_status(record: dict, temporal: str, content_quality: str) -> str:
    material = record.get("material_type") or "needs_review"
    if material == "formal_policy" and temporal in {"current_window", "recent_reference"} and content_quality == "usable_excerpt":
        return "answer_ready"
    if record.get("answer_eligibility") == "review_required":
        return "review_required"
    if material in {"result_notice", "news_activity"}:
        return "context_only" if temporal != "historical_reference" else "archive_only"
    return "archive_only"


def user_intents(material_type: str, topic: str) -> list[str]:
    base = {
        "formal_policy": ["查询条件", "解释规则", "判断影响"],
        "action_notice": ["查询流程", "准备材料", "查询时间"],
        "result_notice": ["查询往年结果", "核验项目存在"],
        "news_activity": ["了解学院动态", "查找相关活动"],
    }.get(material_type, ["补充背景"])
    if topic == "employment_and_career":
        return list(dict.fromkeys(["查找就业信息", *base]))
    return base


def authority_level(url: str, owner: str) -> str:
    host = urlparse(url).hostname or ""
    if host.endswith("gov.cn"):
        return "government_official"
    if owner in {"学校主站", "学生工作部", "研究生院"}:
        return "school_official"
    if host.endswith("sdfmu.edu.cn"):
        return "college_or_unit_official"
    return "external_needs_review"


def build_card(record: dict) -> dict:
    title = clean_title(record.get("title"))
    url = norm_text(record.get("source_url"))
    owner = norm_text(record.get("source_owner")) or "发布单位待核实"
    excerpt, content_quality = clean_content(record.get("title"), record.get("content_excerpt"), title)
    text = f"{title} {excerpt[:1600]}"
    topic = topic_for(record)
    temporal = temporal_status(record)
    material = norm_text(record.get("material_type")) or "needs_review"
    raw_id = f"{title}|{url}"
    return {
        "id": "kb-" + hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:16],
        "title": title or "未命名官方资料",
        "topic": topic,
        "subtopics": subtopics_for(topic, text),
        "user_intents": user_intents(material, topic),
        "student_scope": student_scope(text),
        "college": owner if "学院" in owner else "全校或直属单位",
        "campus": campus_scope(text),
        "source_owner": owner,
        "source_url": url,
        "published_at": norm_text(record.get("published_at")) or "unknown",
        "material_type": material,
        "authority_level": authority_level(url, owner),
        "evidence_role": evidence_role(material),
        "answer_status": answer_status(record, temporal, content_quality),
        "temporal_status": temporal,
        "content_quality": content_quality,
        "effective_scope_note": "仅按原文标明的学生类型、学院、校区和学年使用；未标明时不自动扩大为全校现行规则。",
        "content_excerpt": excerpt[:1800],
        "content_sha256": norm_text(record.get("content_sha256")),
    }


def dedupe(records: list[dict]) -> list[dict]:
    chosen = {}
    for record in records:
        key = norm_text(record.get("source_url")) or norm_text(record.get("normalized_title_key")) or norm_text(record.get("title"))
        current = chosen.get(key)
        if not current or len(norm_text(record.get("content_excerpt"))) > len(norm_text(current.get("content_excerpt"))):
            chosen[key] = record
    return list(chosen.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    source_records = payload.get("records") or []
    unique_records = dedupe(source_records)
    cards = [build_card(record) for record in unique_records]
    cards.sort(key=lambda item: (item["topic"], item["published_at"], item["title"]), reverse=True)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = args.output_dir / "catalog.jsonl"
    catalog_path.write_text("".join(json.dumps(card, ensure_ascii=False) + "\n" for card in cards), encoding="utf-8")

    by_topic = defaultdict(lambda: {"total": 0, "answer_ready": 0, "review_required": 0, "context_only": 0, "archive_only": 0})
    for card in cards:
        by_topic[card["topic"]]["total"] += 1
        by_topic[card["topic"]][card["answer_status"]] += 1

    topic_index = {
        "version": "2026-08-10",
        "total": len(cards),
        "topics": [{"topic": topic, **counts} for topic, counts in sorted(by_topic.items())],
    }
    (args.output_dir / "topic-index.json").write_text(json.dumps(topic_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status_counts = Counter(card["answer_status"] for card in cards)
    role_counts = Counter(card["evidence_role"] for card in cards)
    temporal_counts = Counter(card["temporal_status"] for card in cards)
    content_quality_counts = Counter(card["content_quality"] for card in cards)
    missing_url = [card["id"] for card in cards if not card["source_url"]]
    report = {
        "generated_from": str(args.input),
        "source_count": len(source_records),
        "deduplicated_count": len(cards),
        "duplicate_count": len(source_records) - len(cards),
        "answer_status": dict(sorted(status_counts.items())),
        "evidence_roles": dict(sorted(role_counts.items())),
        "temporal_status": dict(sorted(temporal_counts.items())),
        "content_quality": dict(sorted(content_quality_counts.items())),
        "topic_count": len(by_topic),
        "missing_source_url_count": len(missing_url),
        "missing_source_url_ids": missing_url[:50],
        "release_note": "answer_ready 可进入影子评测；review_required 需人工核对原文；context_only/archive_only 不可单独支撑现行规则。",
    }
    (args.output_dir / "quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"generated {len(cards)} cards from {len(source_records)} records")


if __name__ == "__main__":
    main()
