"""Build user-facing, traceable evidence from Dify retriever resources."""

from __future__ import annotations

from collections.abc import Iterable
import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kb_entry import KbEntry


GOVERNMENT_OFFICIAL_HOSTS = {
    "www.gov.cn",
    "www.moe.gov.cn",
    "www.12371.cn",
    "fuwu.12371.cn",
}


ANSWER_DISCLAIMER = (
    "本答复由医小管产品团队基于学校及相关单位公开资料整理生成，"
    "仅供办事参考，不构成官方解释；具体要求请以学校、学院当年度正式通知"
    "及负责部门答复为准。"
)


# Compatibility for documents already indexed in Dify before source_url was
# added to the precision-pack frontmatter. Keep this deliberately explicit:
# only titles matched to a manually verified official article gain a link.
LEGACY_OFFICIAL_SOURCE_ALIASES = {
    "关于评选20242025学年校级综合奖学金的通知模板版": {
        "title": "2024—2025学年校级综合奖学金评选通知",
        "source_url": "https://sa.sdfmu.edu.cn/info/1341/21131.htm",
        "published_at": "2025-11-18",
        "authority_level": "school",
    },
    "20242025学年校级综合奖学金评选条件": {
        "title": "2024—2025学年校级综合奖学金评选通知",
        "source_url": "https://sa.sdfmu.edu.cn/info/1341/21131.htm",
        "published_at": "2025-11-18",
        "authority_level": "school",
    },
}


def _normalized_legacy_title(value: str | None) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", str(value or "").lower())


def _legacy_official_source(title: str | None) -> dict | None:
    return LEGACY_OFFICIAL_SOURCE_ALIASES.get(_normalized_legacy_title(title))


def _metadata(resource: dict) -> dict:
    value = resource.get("metadata")
    native = value if isinstance(value, dict) else {}
    # Dify text documents keep our source metadata in YAML-like frontmatter.
    # Parse the conservative scalar subset so every new precision pack gains
    # traceable links without a frontend-specific source catalogue.
    content = str(resource.get("content") or "")
    frontmatter: dict[str, str | None] = {}
    if content.startswith("---\n"):
        parts = content.split("---", 2)
        if len(parts) == 3:
            for line in parts[1].splitlines():
                if ":" not in line:
                    continue
                key, raw = line.split(":", 1)
                key = key.strip()
                raw = raw.strip().strip("\"'")
                if key and re.fullmatch(r"[a-z][a-z0-9_]*", key):
                    frontmatter[key] = None if raw in {"", "null", "~"} else raw
    return {**frontmatter, **native}


def _content_heading(content: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def _first(*values):
    return next((value for value in values if value not in (None, "")), None)


def classify_source(url: str | None, metadata: dict) -> tuple[str, str, bool]:
    """Return (source_type, display_label, verified)."""
    verification_status = str(metadata.get("verification_status") or "").lower()
    if "pending_official" in verification_status or "pending_public" in verification_status:
        return "knowledge_base", "校内执行口径·正式文件待补", False
    hostname = (urlparse(url).hostname or "").lower() if url else ""
    if hostname == "sdfmu.edu.cn" or hostname.endswith(".sdfmu.edu.cn"):
        level = str(metadata.get("authority_level") or "")
        label = "学院官网" if level == "college" else "学校官网"
        return "official_web", label, True
    if hostname in GOVERNMENT_OFFICIAL_HOSTS:
        return "official_web", "权威政策来源", True
    if hostname == "mp.weixin.qq.com":
        if metadata.get("verified_official_account") is True:
            return "official_wechat", "已核验公众号", True
        return "wechat_pending", "公众号原文·主体待核验", False
    return "knowledge_base", "校园知识库", False


def build_source_item(resource: dict, entry: KbEntry | None = None) -> dict:
    entry_meta = getattr(entry, "governance_metadata", None)
    if not isinstance(entry_meta, dict):
        entry_meta = {}
    # Retriever frontmatter is closest to the cited segment and therefore
    # takes precedence over the inventory-level governance record.
    meta = {**entry_meta, **_metadata(resource)}
    raw_title = _first(
        meta.get("source_title"),
        _content_heading(str(resource.get("content") or "")),
        resource.get("document_name"),
        getattr(entry, "title", None),
        "未命名资料",
    )
    source_url = _first(
        meta.get("source_url"),
        meta.get("url"),
        getattr(entry, "source_url", None),
    )
    legacy_source = _legacy_official_source(str(raw_title)) if not source_url else None
    if legacy_source:
        source_url = legacy_source["source_url"]
        meta = {**legacy_source, **meta}
    source_type, source_label, verified = classify_source(source_url, meta)
    published_at = _first(
        meta.get("source_published_at"),
        meta.get("published_at"),
        meta.get("publish_date"),
        meta.get("date"),
    )
    freshness = _first(meta.get("freshness"), getattr(entry, "freshness", None))
    effective_status = _first(
        meta.get("effective_status"),
        {
            "current-year": "current",
            "stable": "stable",
            "time-bound": "time-sensitive",
            "expired": "historical",
        }.get(str(freshness or "")),
    )
    source_paths = getattr(entry, "source_paths", None)
    if not source_paths:
        sources = meta.get("sources")
        source_paths = [
            str(item.get("path"))
            for item in sources or []
            if isinstance(item, dict) and item.get("path")
        ]
    return {
        "document_id": _first(resource.get("document_id"), getattr(entry, "dify_document_id", None)),
        "dataset_id": _first(resource.get("dataset_id"), getattr(entry, "dify_dataset_id", None)),
        "title": legacy_source["title"] if legacy_source else raw_title,
        "score": resource.get("score", 0),
        "content": (resource.get("content") or "")[:600],
        "source_url": source_url,
        "original_source": getattr(entry, "original_source", None),
        "category": _first(meta.get("category"), getattr(entry, "category", None)),
        "campus": _first(meta.get("campus"), getattr(entry, "campus", None)),
        "college": meta.get("college"),
        "published_at": published_at,
        "last_verified": meta.get("last_verified"),
        "academic_year": meta.get("academic_year"),
        "effective_status": effective_status,
        "freshness": freshness,
        "policy_level": _first(meta.get("authority_level"), meta.get("policy_level")),
        "source_paths": list(source_paths or []),
        "review_required": bool(meta.get("policy_review_required", False)),
        "screenshot_url": meta.get("screenshot_url"),
        "attachment_url": meta.get("attachment_url"),
        "source_type": source_type,
        "source_label": source_label,
        "verified": verified,
    }


def sort_sources(sources: Iterable[dict]) -> list[dict]:
    authority = {
        "official_web": 3,
        "official_wechat": 2,
        "knowledge_base": 1,
        "wechat_pending": 0,
    }
    return sorted(
        sources,
        key=lambda item: (
            str(item.get("published_at") or ""),
            authority.get(str(item.get("source_type") or ""), 0),
            float(item.get("score") or 0),
        ),
        reverse=True,
    )


def _college_key(value: str | None) -> str:
    if not value:
        return ""
    return str(value).replace("（", "(").split("(", 1)[0].replace(" ", "").strip()


def filter_for_college(sources: Iterable[dict], user_college: str | None) -> list[dict]:
    """Keep school-wide/legacy-unscoped sources and the user's own college."""
    wanted = _college_key(user_college)
    filtered: list[dict] = []
    for source in sources:
        college = str(source.get("college") or "").strip()
        if not college or college in {"全校", "校级"}:
            filtered.append(source)
            continue
        if wanted and _college_key(college) == wanted:
            filtered.append(source)
    return filtered


def filter_for_named_intent(sources: Iterable[dict], query: str | None) -> list[dict]:
    """Hide evidence for a different named award or honour."""
    items = list(sources)
    normalized = str(query or "").replace(" ", "")
    exclusions: tuple[str, ...] = ()
    required: tuple[str, ...] = ()
    if "校级优秀学生" in normalized:
        required = ("校级优秀学生",)
        exclusions = ("弘毅", "综合奖学金", "励志奖学金")
    elif "校级综合奖学金" in normalized or "综合奖学金" in normalized:
        required = ("综合奖学金",)
        exclusions = ("弘毅", "优秀学生", "励志奖学金")
    elif "弘毅" in normalized:
        required = ("弘毅",)
        exclusions = ("综合奖学金", "校级优秀学生")
    elif any(term in normalized for term in ("生源地助学贷款", "毕业确认")):
        required = ("生源地助学贷款毕业确认",)
    elif any(term in normalized for term in ("困难学生库", "突发变故", "困难认定复查")):
        required = ("家庭经济困难认定复查",)
    elif "勤工助学" in normalized:
        required = ("校内勤工助学",)
    elif any(term in normalized.lower() for term in ("四六级", "cet")):
        required = ("四六级报名",)
    if not required:
        return items
    matched = [
        source for source in items
        if any(term in str(source.get("title") or "") for term in required)
        and not any(term in str(source.get("title") or "") for term in exclusions)
    ]
    return matched or items


async def build_source_evidence(
    db: AsyncSession,
    resources: list[dict],
    *,
    user_college: str | None = None,
    query: str | None = None,
) -> list[dict]:
    """Enrich Dify evidence with the local Dify-document/source mapping."""
    document_ids = [
        str(resource["document_id"])
        for resource in resources
        if resource.get("document_id")
    ]
    entries: dict[str, KbEntry] = {}
    if document_ids:
        result = await db.execute(
            select(KbEntry).where(KbEntry.dify_document_id.in_(document_ids))
        )
        entries = {entry.dify_document_id: entry for entry in result.scalars().all()}

    evidence = [
        build_source_item(resource, entries.get(str(resource.get("document_id") or "")))
        for resource in resources
    ]
    scoped = filter_for_college(evidence, user_college)
    return sort_sources(filter_for_named_intent(scoped, query))
