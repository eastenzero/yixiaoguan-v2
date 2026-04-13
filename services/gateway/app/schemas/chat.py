from pydantic import BaseModel, Field
from typing import Optional


class ChatSendRequest(BaseModel):
    """学生发送消息"""
    conv_id: int = Field(..., description="会话 ID")
    content: str = Field(..., min_length=1, max_length=4000, description="消息内容")


class ChatSendResponse(BaseModel):
    """非流式响应（teacher_serving 时）"""
    message_id: int
    conv_id: int
    sender_type: str
    content: str
    created_at: str
