from datetime import UTC, datetime
from hashlib import sha256
from types import SimpleNamespace

from fastapi import HTTPException
from sqlalchemy import desc, or_, select
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


async def create_knowledge_draft(
    db: AsyncSession,
    *,
    current_user: User,
    unanswered_question_id: int,
    raw_answer: str,
    scope: str,
    scope_value: int | None,
) -> tuple[KbSuggestion, str]:
    scope_enum = _normalize_scope(scope)
    college_id, normalized_scope_value = _validate_scope(
        current_user,
        scope=scope_enum,
        scope_value=scope_value,
    )

    result = await db.execute(
        select(UnansweredQuestion).where(UnansweredQuestion.id == unanswered_question_id)
    )
    unanswered = result.scalar_one_or_none()
    if not unanswered:
        raise HTTPException(status_code=404, detail="待补问题不存在")

    if current_user.role == UserRole.teacher and unanswered.college_id not in {None, current_user.college_id}:
        raise HTTPException(status_code=403, detail="不能处理其他学院的待补问题")

    scope_label = _scope_label(scope_enum, normalized_scope_value)
    polished_content = await polish_knowledge_content(
        question=unanswered.question_text,
        raw_answer=raw_answer,
        scope_label=scope_label,
    )
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
