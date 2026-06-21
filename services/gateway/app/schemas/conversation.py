from pydantic import BaseModel
from datetime import datetime
from pydantic import Field, field_validator


class CreateConversationRequest(BaseModel):
    title: str | None = None   # 可选，默认取第一条消息摘要


class ConversationResponse(BaseModel):
    id: int
    student_id: int
    teacher_id: int | None
    status: str
    dify_conversation_id: str | None = None
    title: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
    last_read_at: datetime | None = None
    # joined fields — populated in service layer via batch user lookup
    student_name: str | None = None
    teacher_name: str | None = None

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be empty")
        return stripped


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_type: str       # student | ai | teacher | system
    sender_id: int | None
    content: str
    metadata_: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int


class UnreadSummaryItem(BaseModel):
    conv_id: int
    title: str
    status: str
    unread_count: int
    last_message_at: datetime | None = None
    last_message_sender_type: str | None = None  # student | ai | teacher | system | None
    last_read_at: datetime | None = None

    class Config:
        from_attributes = True


class UnreadSummaryResponse(BaseModel):
    items: list[UnreadSummaryItem]
    total_unread: int
