from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UnansweredTopItemResponse(BaseModel):
    id: int
    question_text: str
    hit_count: int
    latest_at: datetime
    college_id: int | None = None
    class_id: int | None = None
    sample_conv_ids: list[int] = Field(default_factory=list)


class UnansweredTopResponse(BaseModel):
    items: list[UnansweredTopItemResponse]
    total: int


class CreateKnowledgeDraftRequest(BaseModel):
    unanswered_question_id: int
    raw_answer: str
    scope: Literal["class", "college", "global"] = "college"
    scope_value: int | None = None

    @field_validator("raw_answer")
    @classmethod
    def validate_raw_answer(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("答复内容不能为空")
        return normalized


class KnowledgeDraftEntryResponse(BaseModel):
    id: int
    title: str
    content: str
    raw_content: str | None = None
    scope: str
    scope_value: int | None = None
    representative_query: str
    status: str
    college_id: int | None = None
    submitted_by: int
    reject_reason: str | None = None
    dify_document_id: str | None = None
    created_at: datetime
    published_at: datetime | None = None
    reviewed_at: datetime | None = None


class CreateKnowledgeDraftResponse(BaseModel):
    entry: KnowledgeDraftEntryResponse
    publish_mode: Literal["published", "pending_review"]


class PendingKnowledgeReviewResponse(BaseModel):
    items: list[KnowledgeDraftEntryResponse]
    total: int


class KnowledgeEntryListResponse(BaseModel):
    """
    GET /api/v1/knowledge/entries 响应。
    非 admin 返回当前教师提交的条目（"我的知识"）；admin 返回全部。
    """

    items: list[KnowledgeDraftEntryResponse]
    total: int


class RejectKnowledgeReviewRequest(BaseModel):
    reject_reason: str | None = None

    @field_validator("reject_reason")
    @classmethod
    def normalize_reject_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
