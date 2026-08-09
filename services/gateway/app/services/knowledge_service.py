from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.kb_entry import KbEntry
from app.models.knowledge import (
    CollegeDataset,
    KbSuggestion,
    KnowledgeScope,
    SuggestionSource,
    SuggestionStatus,
    UnansweredQuestion,
)
from app.models.user import User, UserRole
from app.services.dify_client import dify_client


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def list_unanswered_top(
    db: AsyncSession,
    current_user: User,
    *,
    limit: int,
) -> tuple[list[UnansweredQuestion], int]:
    stmt = select(UnansweredQuestion).where(UnansweredQuestion.is_resolved.is_(False))

    if current_user.role == UserRole.teacher:
        stmt = stmt.where(
            or_(
                UnansweredQuestion.college_id == current_user.college_id,
                UnansweredQuestion.college_id.is_(None),
            )
        )
    elif current_user.role != UserRole.admin:
        return [], 0

    stmt = stmt.order_by(
        desc(UnansweredQuestion.hit_count),
        desc(UnansweredQuestion.updated_at),
        desc(UnansweredQuestion.id),
    ).limit(limit)

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, len(items)


def _normalize_scope(scope: str) -> KnowledgeScope:
    if scope == "class":
        return KnowledgeScope.class_
    if scope == "college":
        return KnowledgeScope.college
    if scope == "global":
        return KnowledgeScope.global_
    raise HTTPException(status_code=400, detail="无效的知识范围")


def _scope_label(scope: KnowledgeScope, scope_value: int | None) -> str:
    if scope == KnowledgeScope.class_:
        return f"班级 {scope_value or ''}".strip()
    if scope == KnowledgeScope.college:
        return f"学院 {scope_value or ''}".strip()
    return "全校"


def _build_fallback_polished_content(*, question: str, raw_answer: str, scope_label: str) -> str:
    return f"适用范围：{scope_label}\n\n问题：{question}\n\n答复：{raw_answer}"


async def polish_knowledge_content(*, question: str, raw_answer: str, scope_label: str) -> str:
    try:
        return await dify_client.polish_text(
            question=question,
            raw_answer=raw_answer,
            scope_label=scope_label,
        )
    except Exception:
        return _build_fallback_polished_content(
            question=question,
            raw_answer=raw_answer,
            scope_label=scope_label,
        )


async def _load_unanswered_question(
    db: AsyncSession,
    current_user: User,
    *,
    unanswered_question_id: int,
) -> UnansweredQuestion:
    result = await db.execute(
        select(UnansweredQuestion).where(UnansweredQuestion.id == unanswered_question_id)
    )
    unanswered = result.scalar_one_or_none()
    if not unanswered:
        raise HTTPException(status_code=404, detail="待补问题不存在")

    if current_user.role == UserRole.teacher and unanswered.college_id not in {None, current_user.college_id}:
        raise HTTPException(status_code=403, detail="不能处理其他学院的待补问题")

    return unanswered


async def _resolve_dataset_id(db: AsyncSession, *, scope: KnowledgeScope, scope_value: int | None, user: User) -> str:
    if scope == KnowledgeScope.global_:
        if not settings.dify_global_dataset_id:
            raise HTTPException(status_code=500, detail="未配置全局知识库数据集")
        return settings.dify_global_dataset_id

    target_college_id = user.college_id if scope == KnowledgeScope.college else user.college_id
    if target_college_id is None:
        raise HTTPException(status_code=400, detail="当前教师未绑定学院，无法发布知识")

    result = await db.execute(
        select(CollegeDataset).where(CollegeDataset.college_id == target_college_id)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=500, detail="未配置学院知识库数据集")
    return mapping.dify_dataset_id


def _validate_scope(current_user: User, *, scope: KnowledgeScope, scope_value: int | None) -> tuple[int | None, int | None]:
    if current_user.role not in {UserRole.teacher, UserRole.admin}:
        raise HTTPException(status_code=403, detail="仅教师或管理员可提交知识答复")

    college_id = current_user.college_id
    if scope == KnowledgeScope.college:
        if college_id is None:
            raise HTTPException(status_code=400, detail="当前教师未绑定学院，无法按学院发布")
        if scope_value is not None and scope_value != college_id:
            raise HTTPException(status_code=403, detail="教师不能发布到其他学院")
        return college_id, college_id

    if scope == KnowledgeScope.class_:
        if current_user.class_id is None:
            raise HTTPException(status_code=403, detail="当前教师未绑定班级，无法按班级发布")
        if scope_value is None:
            scope_value = current_user.class_id
        if scope_value != current_user.class_id:
            raise HTTPException(status_code=403, detail="教师不能发布到其他班级")
        return college_id, scope_value

    return college_id, None


def serialize_suggestion(entry: KbSuggestion) -> dict:
    return {
        "id": entry.id,
        "title": entry.title,
        "content": entry.content,
        "raw_content": entry.raw_content,
        "scope": entry.scope.value,
        "scope_value": entry.scope_value,
        "representative_query": entry.representative_query,
        "status": entry.status.value,
        "college_id": entry.college_id,
        "submitted_by": entry.submitted_by,
        "reject_reason": entry.reject_reason,
        "dify_document_id": entry.dify_document_id,
        "created_at": entry.created_at,
        "published_at": entry.published_at,
        "reviewed_at": entry.reviewed_at,
    }


def _ensure_admin(current_user: User) -> None:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="仅管理员可执行审核操作")


async def list_pending_reviews(
    db: AsyncSession,
    current_user: User,
    *,
    limit: int,
) -> tuple[list[KbSuggestion], int]:
    _ensure_admin(current_user)
    stmt = (
        select(KbSuggestion)
        .where(
            KbSuggestion.scope == KnowledgeScope.global_,
            KbSuggestion.status == SuggestionStatus.pending,
        )
        .order_by(desc(KbSuggestion.created_at), desc(KbSuggestion.id))
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, len(items)


async def _publish_suggestion_to_dify(db: AsyncSession, entry: KbSuggestion) -> str:
    dataset_id = await _resolve_dataset_id(
        db,
        scope=entry.scope,
        scope_value=entry.scope_value,
        user=SimpleNamespace(college_id=entry.college_id),
    )
    document = await dify_client.create_document(
        dataset_id=dataset_id,
        title=entry.title,
        content=entry.content,
    )
    document_id = str(document.get("document", {}).get("id", "")).strip()
    if not document_id:
        raise HTTPException(status_code=502, detail="Dify 发布返回缺少文档 ID")

    db.add(
        KbEntry(
            dify_document_id=document_id,
            dify_dataset_id=dataset_id,
            title=entry.title,
            category=None,
            tags=None,
            original_source="teacher-kb-review",
            source_url=None,
            material_id=str(entry.id),
            campus=None,
            original_filename=None,
        )
    )
    return document_id


async def approve_pending_review(
    db: AsyncSession,
    *,
    current_user: User,
    suggestion_id: int,
) -> KbSuggestion:
    _ensure_admin(current_user)
    result = await db.execute(select(KbSuggestion).where(KbSuggestion.id == suggestion_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="待审核知识不存在")
    if entry.status != SuggestionStatus.pending or entry.scope != KnowledgeScope.global_:
        raise HTTPException(status_code=400, detail="该知识条目不可重复审核")

    try:
        document_id = await _publish_suggestion_to_dify(db, entry)
        entry.status = SuggestionStatus.approved
        entry.reviewed_by = current_user.id
        entry.reviewed_at = _utcnow_naive()
        entry.published_at = _utcnow_naive()
        entry.reject_reason = None
        entry.dify_document_id = document_id
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=502, detail=f"Dify 发布失败: {exc}") from exc

    await db.refresh(entry)
    return entry


async def reject_pending_review(
    db: AsyncSession,
    *,
    current_user: User,
    suggestion_id: int,
    reject_reason: str | None,
) -> KbSuggestion:
    _ensure_admin(current_user)
    result = await db.execute(select(KbSuggestion).where(KbSuggestion.id == suggestion_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="待审核知识不存在")
    if entry.status != SuggestionStatus.pending or entry.scope != KnowledgeScope.global_:
        raise HTTPException(status_code=400, detail="该知识条目不可重复审核")

    entry.status = SuggestionStatus.rejected
    entry.reviewed_by = current_user.id
    entry.reviewed_at = _utcnow_naive()
    entry.reject_reason = reject_reason or "管理员驳回"
    await db.commit()
    await db.refresh(entry)
    return entry


async def create_knowledge_draft_preview(
    db: AsyncSession,
    *,
    current_user: User,
    unanswered_question_id: int,
    raw_answer: str,
    scope: str,
    scope_value: int | None,
) -> dict:
    scope_enum = _normalize_scope(scope)
    college_id, normalized_scope_value = _validate_scope(
        current_user,
        scope=scope_enum,
        scope_value=scope_value,
    )
    unanswered = await _load_unanswered_question(
        db,
        current_user,
        unanswered_question_id=unanswered_question_id,
    )

    scope_label = _scope_label(scope_enum, normalized_scope_value)
    polished_content = await polish_knowledge_content(
        question=unanswered.question_text,
        raw_answer=raw_answer,
        scope_label=scope_label,
    )

    return {
        "unanswered_question_id": unanswered.id,
        "title": unanswered.question_text[:255],
        "content": polished_content,
        "raw_content": raw_answer,
        "scope": scope_enum.value,
        "scope_value": normalized_scope_value,
        "scope_label": scope_label,
        "representative_query": unanswered.question_text,
        "college_id": college_id,
        "publish_mode": "requires_confirmation",
    }


def _build_kb_entry_content(entry: KbEntry) -> str:
    lines: list[str] = []
    if entry.category:
        lines.append(f"分类：{entry.category}")
    if entry.tags:
        lines.append(f"标签：{' / '.join(entry.tags)}")
    if entry.campus:
        lines.append(f"校区：{entry.campus}")
    if entry.original_source:
        lines.append(f"来源：{entry.original_source}")
    if entry.original_filename:
        lines.append(f"原始文件：{entry.original_filename}")
    if entry.material_id:
        lines.append(f"素材编号：{entry.material_id}")
    if entry.source_url:
        lines.append(f"来源链接：{entry.source_url}")
    lines.append(f"Dify 文档 ID：{entry.dify_document_id}")
    return "\n".join(lines)


def _governance_metadata(entry: KbEntry) -> dict:
    value = getattr(entry, "governance_metadata", None)
    return value if isinstance(value, dict) else {}


def _iso_value(value) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if value in (None, ""):
        return None
    return str(value)


def _source_paths(entry: KbEntry, metadata: dict) -> list[str]:
    direct = getattr(entry, "source_paths", None)
    if isinstance(direct, list) and direct:
        return [str(value) for value in direct if value]
    sources = metadata.get("sources")
    if not isinstance(sources, list):
        return []
    return [str(item.get("path")) for item in sources if isinstance(item, dict) and item.get("path")]


def _policy_level(entry: KbEntry, metadata: dict) -> str | None:
    explicit = metadata.get("authority_level") or metadata.get("policy_level")
    if explicit:
        return str(explicit)
    scope = str(getattr(entry, "governance_scope", None) or "")
    return {"global": "school", "college": "college"}.get(scope)


def _effective_status(entry: KbEntry, metadata: dict) -> str:
    explicit = metadata.get("effective_status")
    if explicit:
        return str(explicit)
    return {
        "current-year": "current",
        "stable": "stable",
        "time-bound": "time-sensitive",
        "expired": "historical",
    }.get(str(getattr(entry, "freshness", None) or ""), "unknown")


def serialize_kb_entry(entry: KbEntry) -> dict:
    scope = "global" if entry.dify_dataset_id == settings.dify_global_dataset_id else "college"
    metadata = _governance_metadata(entry)
    source_types = metadata.get("source_types")
    if not isinstance(source_types, list):
        source_types = []
    verified_at = metadata.get("last_verified") or getattr(entry, "reviewed_at", None)
    source_published_at = metadata.get("source_published_at") or metadata.get("published_at")
    governed_content = getattr(entry, "content", None)
    return {
        "id": entry.id,
        "title": entry.title,
        "content": governed_content or _build_kb_entry_content(entry),
        "raw_content": getattr(entry, "raw_content", None),
        "scope": scope,
        "scope_value": None,
        "representative_query": entry.original_source or entry.category or entry.original_filename or "真实知识库条目",
        "status": "published",
        "college_id": getattr(entry, "college_id", None),
        "submitted_by": 0,
        "reject_reason": None,
        "dify_document_id": entry.dify_document_id,
        "dify_dataset_id": entry.dify_dataset_id,
        "source_type": "kb_entry",
        "category": entry.category,
        "tags": entry.tags,
        "original_source": entry.original_source,
        "source_url": entry.source_url,
        "material_id": entry.material_id,
        "campus": entry.campus,
        "original_filename": entry.original_filename,
        "created_at": entry.created_at,
        "published_at": getattr(entry, "published_at", None) or entry.created_at,
        "reviewed_at": getattr(entry, "reviewed_at", None),
        "verified_at": _iso_value(verified_at),
        "source_published_at": _iso_value(source_published_at),
        "freshness": str(getattr(entry, "freshness", None) or "unclassified"),
        "effective_status": _effective_status(entry, metadata),
        "policy_level": _policy_level(entry, metadata),
        "audience": list(getattr(entry, "audience", None) or []),
        "source_paths": _source_paths(entry, metadata),
        "source_types": [str(value) for value in source_types if value],
        "review_required": bool(metadata.get("policy_review_required", False)),
    }


async def _college_dataset_id(db: AsyncSession, college_id: int) -> str | None:
    result = await db.execute(
        select(CollegeDataset.dify_dataset_id).where(CollegeDataset.college_id == college_id)
    )
    return result.scalar_one_or_none()


async def _visible_kb_dataset_ids(db: AsyncSession, current_user: User) -> set[str] | None:
    if current_user.role == UserRole.admin:
        return None
    if current_user.role != UserRole.teacher:
        raise HTTPException(status_code=403, detail="仅教师或管理员可查看知识库")

    dataset_ids: set[str] = set()
    if settings.dify_global_dataset_id:
        dataset_ids.add(settings.dify_global_dataset_id)
    if current_user.college_id is not None:
        college_dataset_id = await _college_dataset_id(db, current_user.college_id)
        if college_dataset_id:
            dataset_ids.add(college_dataset_id)
    return dataset_ids


def summarize_knowledge_overview(entries: list[KbEntry]) -> dict:
    freshness_counts: dict[str, int] = {}
    verified_values: list[str] = []
    source_traceable_count = 0
    review_required_count = 0
    student_visible_count = 0

    for entry in entries:
        metadata = _governance_metadata(entry)
        freshness = str(getattr(entry, "freshness", None) or "unclassified")
        freshness_counts[freshness] = freshness_counts.get(freshness, 0) + 1

        verified_at = _iso_value(metadata.get("last_verified") or getattr(entry, "reviewed_at", None))
        if verified_at:
            verified_values.append(verified_at)
        if entry.source_url or _source_paths(entry, metadata):
            source_traceable_count += 1
        if metadata.get("policy_review_required") is True:
            review_required_count += 1
        if bool(getattr(entry, "student_rag_visible", False)):
            student_visible_count += 1

    return {
        "total": len(entries),
        "verified_count": len(verified_values),
        "latest_verified_at": max(verified_values) if verified_values else None,
        "student_visible_count": student_visible_count,
        "source_traceable_count": source_traceable_count,
        "review_required_count": review_required_count,
        "freshness_counts": freshness_counts,
        "notice": "核验日期来自知识治理清单；具体政策以学校、学院当年度正式通知及负责部门答复为准。",
    }


async def get_knowledge_overview(db: AsyncSession, current_user: User) -> dict:
    visible_dataset_ids = await _visible_kb_dataset_ids(db, current_user)
    stmt = select(KbEntry)
    if visible_dataset_ids is not None:
        if not visible_dataset_ids:
            return summarize_knowledge_overview([])
        stmt = stmt.where(KbEntry.dify_dataset_id.in_(visible_dataset_ids))
    result = await db.execute(stmt)
    return summarize_knowledge_overview(list(result.scalars().all()))


async def list_knowledge_entries(
    db: AsyncSession,
    current_user: User,
    *,
    title: str | None,
    category: str | None,
    campus: str | None,
    source: str | None,
    college_id: int | None,
    page_num: int,
    page_size: int,
) -> tuple[list[KbEntry], int]:
    visible_dataset_ids = await _visible_kb_dataset_ids(db, current_user)
    filters = []
    if visible_dataset_ids is not None:
        if not visible_dataset_ids:
            return [], 0
        filters.append(KbEntry.dify_dataset_id.in_(visible_dataset_ids))

    if college_id is not None:
        target_dataset_id = await _college_dataset_id(db, college_id)
        if not target_dataset_id:
            return [], 0
        if visible_dataset_ids is not None and target_dataset_id not in visible_dataset_ids:
            return [], 0
        filters.append(KbEntry.dify_dataset_id == target_dataset_id)

    keyword = (title or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                KbEntry.title.ilike(pattern),
                KbEntry.category.ilike(pattern),
                KbEntry.original_source.ilike(pattern),
                KbEntry.source_url.ilike(pattern),
                KbEntry.material_id.ilike(pattern),
                KbEntry.original_filename.ilike(pattern),
            )
        )
    category_keyword = (category or "").strip()
    if category_keyword:
        filters.append(KbEntry.category.ilike(f"%{category_keyword}%"))
    campus_keyword = (campus or "").strip()
    if campus_keyword:
        filters.append(KbEntry.campus.ilike(f"%{campus_keyword}%"))
    source_keyword = (source or "").strip()
    if source_keyword:
        source_pattern = f"%{source_keyword}%"
        filters.append(
            or_(
                KbEntry.original_source.ilike(source_pattern),
                KbEntry.source_url.ilike(source_pattern),
                KbEntry.original_filename.ilike(source_pattern),
                KbEntry.material_id.ilike(source_pattern),
            )
        )

    count_stmt = select(func.count()).select_from(KbEntry)
    stmt = select(KbEntry)
    if filters:
        count_stmt = count_stmt.where(*filters)
        stmt = stmt.where(*filters)

    total_result = await db.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)
    if total == 0:
        return [], 0

    offset = (page_num - 1) * page_size
    result = await db.execute(
        stmt.order_by(desc(KbEntry.created_at), desc(KbEntry.id)).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_knowledge_entry(
    db: AsyncSession,
    current_user: User,
    *,
    entry_id: int,
) -> KbEntry:
    result = await db.execute(select(KbEntry).where(KbEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="知识条目不存在")

    visible_dataset_ids = await _visible_kb_dataset_ids(db, current_user)
    if visible_dataset_ids is not None and entry.dify_dataset_id not in visible_dataset_ids:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return entry


async def create_knowledge_draft(
    db: AsyncSession,
    *,
    current_user: User,
    unanswered_question_id: int,
    raw_answer: str,
    confirmed_content: str | None = None,
    scope: str,
    scope_value: int | None,
) -> tuple[KbSuggestion, str]:
    scope_enum = _normalize_scope(scope)
    college_id, normalized_scope_value = _validate_scope(
        current_user,
        scope=scope_enum,
        scope_value=scope_value,
    )

    unanswered = await _load_unanswered_question(
        db,
        current_user,
        unanswered_question_id=unanswered_question_id,
    )

    if confirmed_content is None:
        raise HTTPException(status_code=400, detail="请先生成润色预览并确认发布内容")

    polished_content = confirmed_content.strip()
    if not polished_content:
        raise HTTPException(status_code=400, detail="确认发布内容不能为空")
    title = unanswered.question_text[:255]
    suggestion = KbSuggestion(
        title=title,
        content=polished_content,
        raw_content=raw_answer,
        source=SuggestionSource.teacher_input,
        source_url=None,
        college_id=college_id,
        scope=scope_enum,
        scope_value=normalized_scope_value,
        representative_query=unanswered.question_text,
        question_hash=unanswered.question_hash or sha256(unanswered.question_text.encode("utf-8")).hexdigest(),
        status=SuggestionStatus.pending if scope_enum == KnowledgeScope.global_ else SuggestionStatus.approved,
        submitted_by=current_user.id,
        reviewed_by=current_user.id if scope_enum != KnowledgeScope.global_ else None,
        reject_reason=None,
        dify_document_id=None,
        published_at=None,
        reviewed_at=_utcnow_naive() if scope_enum != KnowledgeScope.global_ else None,
    )
    db.add(suggestion)
    await db.flush()

    publish_mode = "pending_review"
    if scope_enum != KnowledgeScope.global_:
        try:
            dataset_id = await _resolve_dataset_id(
                db,
                scope=scope_enum,
                scope_value=normalized_scope_value,
                user=current_user,
            )
            document = await dify_client.create_document(
                dataset_id=dataset_id,
                title=title,
                content=polished_content,
            )
            document_id = str(document.get("document", {}).get("id", "")).strip()
            if not document_id:
                raise HTTPException(status_code=502, detail="Dify 发布返回缺少文档 ID")

            db.add(
                KbEntry(
                    dify_document_id=document_id,
                    dify_dataset_id=dataset_id,
                    title=title,
                    category=None,
                    tags=None,
                    original_source="teacher-kb-draft",
                    source_url=None,
                    material_id=str(suggestion.id),
                    campus=None,
                    original_filename=None,
                )
            )
            suggestion.dify_document_id = document_id
            suggestion.status = SuggestionStatus.approved
            suggestion.published_at = _utcnow_naive()
            unanswered.is_resolved = True
            unanswered.kb_suggestion_id = suggestion.id
            publish_mode = "published"
        except HTTPException:
            await db.rollback()
            raise
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=502, detail=f"Dify 发布失败: {exc}") from exc
    else:
        unanswered.kb_suggestion_id = suggestion.id

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(suggestion)
    return suggestion, publish_mode
