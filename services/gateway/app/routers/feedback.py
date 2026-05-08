"""User feedback endpoints (R11)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Message
from app.models.feedback import Feedback
from app.models.unanswered_user_feedback import UnansweredUserFeedback
from app.models.user import User
from app.services.conversation_service import get_conversation
from app.utils.deps import get_current_user

router = APIRouter()


ALLOWED_GRADES = {"grade_1", "grade_2", "grade_3", "grade_4", "grad", "other"}
ALLOWED_CATEGORIES = {
    "scholarship",
    "course",
    "registration",
    "dorm",
    "medical",
    "network",
    "activity",
    "other",
}


class GeneralFeedbackRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    contact: str | None = Field(default=None, max_length=128)
    device_id: str | None = Field(default=None, max_length=64)


class UnansweredFeedbackRequest(BaseModel):
    conv_id: int
    message_id: int
    college_id: int | None = None
    grade: str | None = None
    category: str | None = None
    note: str | None = Field(default=None, max_length=2000)


@router.post("/general")
async def submit_general_feedback(
    body: GeneralFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int | bool]:
    fb = Feedback(
        user_id=current_user.id,
        device_id=body.device_id,
        content=body.content,
        contact=body.contact,
        source="general",
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return {"id": fb.id, "ok": True}


@router.post("/unanswered")
async def submit_unanswered_feedback(
    body: UnansweredFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int | bool]:
    conv = await get_conversation(db, body.conv_id, current_user)
    if conv is None:
        raise HTTPException(404, "conversation not found or not accessible")

    msg = await db.scalar(
        select(Message).where(
            Message.id == body.message_id,
            Message.conversation_id == body.conv_id,
        )
    )
    if msg is None:
        raise HTTPException(404, "message not found in this conversation")

    grade = body.grade if body.grade in ALLOWED_GRADES else None
    category = body.category if body.category in ALLOWED_CATEGORIES else None

    uuf = UnansweredUserFeedback(
        conversation_id=body.conv_id,
        message_id=body.message_id,
        user_id=current_user.id,
        user_provided_college_id=body.college_id,
        user_provided_grade=grade,
        user_provided_category=category,
        user_provided_note=body.note,
        unanswered_question_id=None,
    )
    db.add(uuf)
    await db.commit()
    await db.refresh(uuf)
    return {"id": uuf.id, "ok": True}
