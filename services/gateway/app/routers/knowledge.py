from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.knowledge import (
    CreateKnowledgeDraftRequest,
    CreateKnowledgeDraftResponse,
    KnowledgeBaseEntriesResponse,
    KnowledgeBaseEntryResponse,
    KnowledgeDraftPreviewResponse,
    PendingKnowledgeReviewResponse,
    RejectKnowledgeReviewRequest,
    UnansweredTopItemResponse,
    UnansweredTopResponse,
)
from app.services.knowledge_service import (
    approve_pending_review,
    create_knowledge_draft,
    create_knowledge_draft_preview,
    get_knowledge_entry,
    list_knowledge_entries,
    list_pending_reviews,
    list_unanswered_top,
    reject_pending_review,
    serialize_kb_entry,
    serialize_suggestion,
)
from app.utils.deps import get_current_user

router = APIRouter()


@router.get('/entries', response_model=KnowledgeBaseEntriesResponse)
async def get_knowledge_entries(
    title: str | None = Query(None, description='关键词，匹配标题、来源、原始文件等'),
    category: str | None = Query(None, description='知识分类'),
    campus: str | None = Query(None, description='校区'),
    source: str | None = Query(None, description='来源/素材编号/原始文件'),
    college_id: int | None = Query(None, ge=1, description='学院 ID，对应学院 Dify 数据集'),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await list_knowledge_entries(
        db,
        current_user,
        title=title,
        category=category,
        campus=campus,
        source=source,
        college_id=college_id,
        page_num=pageNum,
        page_size=pageSize,
    )
    return KnowledgeBaseEntriesResponse(
        items=[serialize_kb_entry(item) for item in items],
        total=total,
    )


@router.get('/entries/{entry_id}', response_model=KnowledgeBaseEntryResponse)
async def get_knowledge_entry_detail(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = await get_knowledge_entry(
        db,
        current_user,
        entry_id=entry_id,
    )
    return KnowledgeBaseEntryResponse(**serialize_kb_entry(entry))


@router.get('/unanswered-top', response_model=UnansweredTopResponse)
async def get_unanswered_top(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {UserRole.teacher, UserRole.admin}:
        raise HTTPException(status_code=403, detail='仅教师或管理员可查看待补问题')

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


@router.post('/drafts', response_model=CreateKnowledgeDraftResponse, status_code=201)
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
        confirmed_content=body.confirmed_content,
        scope=body.scope,
        scope_value=body.scope_value,
    )
    return CreateKnowledgeDraftResponse(
        entry=serialize_suggestion(entry),
        publish_mode=publish_mode,
    )


@router.post('/drafts/preview', response_model=KnowledgeDraftPreviewResponse)
async def preview_draft(
    body: CreateKnowledgeDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_knowledge_draft_preview(
        db,
        current_user=current_user,
        unanswered_question_id=body.unanswered_question_id,
        raw_answer=body.raw_answer,
        scope=body.scope,
        scope_value=body.scope_value,
    )


@router.get('/reviews/pending', response_model=PendingKnowledgeReviewResponse)
@router.get('/review/pending', response_model=PendingKnowledgeReviewResponse)
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


@router.post('/reviews/{suggestion_id}/approve', response_model=CreateKnowledgeDraftResponse)
@router.post('/review/{suggestion_id}/approve', response_model=CreateKnowledgeDraftResponse)
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
        publish_mode='published',
    )


@router.post('/reviews/{suggestion_id}/reject', response_model=CreateKnowledgeDraftResponse)
@router.post('/review/{suggestion_id}/reject', response_model=CreateKnowledgeDraftResponse)
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
        publish_mode='pending_review',
    )
