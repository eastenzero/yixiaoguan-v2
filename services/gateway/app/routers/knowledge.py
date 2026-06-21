from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.knowledge import (
    CreateKnowledgeDraftRequest,
    CreateKnowledgeDraftResponse,
    KnowledgeEntryListResponse,
    PendingKnowledgeReviewResponse,
    RejectKnowledgeReviewRequest,
    UnansweredTopItemResponse,
    UnansweredTopResponse,
)
from app.services.knowledge_service import (
    approve_pending_review,
    create_knowledge_draft,
    list_knowledge_entries,
    list_pending_reviews,
    list_unanswered_top,
    reject_pending_review,
    serialize_suggestion,
)
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/entries", response_model=KnowledgeEntryListResponse)
async def get_knowledge_entries(
    title: str | None = Query(None, description="按 title 模糊搜索"),
    pageNum: int = Query(1, ge=1, description="页码（1-indexed）"),
    pageSize: int = Query(20, ge=1, le=100, description="每页条目数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    "我的知识"列表。
    - 非 admin：仅返回当前教师提交的条目（所有状态）
    - admin：返回全部条目
    """
    items, total = await list_knowledge_entries(
        db,
        current_user,
        title=title,
        page_num=pageNum,
        page_size=pageSize,
    )
    return KnowledgeEntryListResponse(
        items=[serialize_suggestion(item) for item in items],
        total=total,
    )


@router.get("/unanswered-top", response_model=UnansweredTopResponse)
async def get_unanswered_top(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {UserRole.teacher, UserRole.admin}:
        raise HTTPException(status_code=403, detail="仅教师或管理员可查看待补问题")

    items, total = await list_unanswered_top(db, current_user, limit=limit)
    return UnansweredTopResponse(
        items=[
            UnansweredTopItemResponse(
                id=item.id,
                question_text=item.question_text,
                hit_count=item.hit_count,
                latest_at=item.updated_at,
                college_id=item.college_id,
                class_id=None,
                sample_conv_ids=list(item.sample_conv_ids or []),
            )
            for item in items
        ],
        total=total,
    )


@router.post("/drafts", response_model=CreateKnowledgeDraftResponse, status_code=201)
async def create_draft(
    body: CreateKnowledgeDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry, publish_mode = await create_knowledge_draft(
        db,
        current_user=current_user,
        unanswered_question_id=body.unanswered_question_id,
        raw_answer=body.raw_answer,
        scope=body.scope,
        scope_value=body.scope_value,
    )
    return CreateKnowledgeDraftResponse(
        entry=serialize_suggestion(entry),
        publish_mode=publish_mode,
    )


@router.get("/reviews/pending", response_model=PendingKnowledgeReviewResponse)
@router.get("/review/pending", response_model=PendingKnowledgeReviewResponse)
async def get_pending_reviews(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await list_pending_reviews(db, current_user, limit=limit)
    return PendingKnowledgeReviewResponse(
        items=[serialize_suggestion(item) for item in items],
        total=total,
    )


@router.post("/reviews/{suggestion_id}/approve", response_model=CreateKnowledgeDraftResponse)
@router.post("/review/{suggestion_id}/approve", response_model=CreateKnowledgeDraftResponse)
async def approve_review(
    suggestion_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await approve_pending_review(
        db,
        current_user=current_user,
        suggestion_id=suggestion_id,
    )
    return CreateKnowledgeDraftResponse(
        entry=serialize_suggestion(entry),
        publish_mode="published",
    )


@router.post("/reviews/{suggestion_id}/reject", response_model=CreateKnowledgeDraftResponse)
@router.post("/review/{suggestion_id}/reject", response_model=CreateKnowledgeDraftResponse)
async def reject_review(
    suggestion_id: int,
    body: RejectKnowledgeReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await reject_pending_review(
        db,
        current_user=current_user,
        suggestion_id=suggestion_id,
        reject_reason=body.reject_reason,
    )
    return CreateKnowledgeDraftResponse(
        entry=serialize_suggestion(entry),
        publish_mode="pending_review",
    )
