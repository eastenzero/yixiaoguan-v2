from pydantic import BaseModel
from datetime import datetime


class CreateConversationRequest(BaseModel):
    title: str | None = None   # 可选，默认取第一条消息摘要


class ConversationResponse(BaseModel):
    id: int
    student_id: int
    teacher_id: int | None
    status: str
    title: str
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    content: str


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
