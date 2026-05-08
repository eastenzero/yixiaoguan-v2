from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import College

router = APIRouter()


@router.get("/colleges")
async def list_colleges(db: AsyncSession = Depends(get_db)):
    """List all colleges. No auth required (used by pilot anonymous frontend)."""
    rows = (
        await db.execute(
            select(College.id, College.name, College.campus).order_by(College.id)
        )
    ).all()
    return [{"id": row.id, "name": row.name, "campus": row.campus} for row in rows]
