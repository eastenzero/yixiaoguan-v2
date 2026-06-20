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
    confirmed_content: str | None = None
    scope: Literal["class", "college", "global"] = "college"
    scope_value: int | None = None

    @field_validator("raw_answer")
    @classmethod
    def validate_raw_answer(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("答复内容不能为空")
        return normalized

    @field_validator("confirmed_content")
    @classmethod
    def validate_confirmed_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("确认发布内容不能为空")
        return normalized


class KnowledgeDraftPreviewResponse(BaseModel):
    unanswered_question_id: int
    title: str
    content: str
    raw_content: str
    scope: str
    scope_value: int | None = None
    scope_label: str
    representative_query: str
    college_id: int | None = None
    publish_mode: Literal["requires_confirmation"] = "requires_confirmation"


class KnowledgeBaseEntryResponse(BaseModel):
    id: int
    title: str
    content: str
    raw_content: str | None = None
    scope: Literal["college", "global"] = "global"
    scope_value: int | None = None
    representative_query: str
    status: Literal["published"] = "published"
    college_id: int | None = None
    submitted_by: int = 0
    reject_reason: str | None = None
    dify_document_id: str
    dify_dataset_id: str
    source_type: Literal["kb_entry"] = "kb_entry"
    category: str | None = None
    tags: list[str] | None = None
    original_source: str | None = None
    source_url: str | None = None
    material_id: str | None = None
    campus: str | None = None
    original_filename: str | None = None
    created_at: datetime
    published_at: datetime | None = None
    reviewed_at: datetime | None = None


class KnowledgeBaseEntriesResponse(BaseModel):
    items: list[KnowledgeBaseEntryResponse]
    total: int


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


class RejectKnowledgeReviewRequest(BaseModel):
    reject_reason: str | None = None

    @field_validator("reject_reason")
    @classmethod
    def normalize_reject_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
