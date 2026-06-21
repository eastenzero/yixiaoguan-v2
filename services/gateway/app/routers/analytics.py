"""
Analytics dashboard API – 教师端数据看板
GET /api/analytics?period=7d|30d|all
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, and_, select, extract, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.deps import get_current_user
from app.models.user import User, College
from app.models.conversation import Conversation, ConversationStatus
from app.models.chat_analytics import ChatAnalytics
from app.models.knowledge import UnansweredQuestion

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ── helpers ──────────────────────────────────────────────

def _period_range(period: str):
    """Return (start, prev_start | None, now) for the requested window.

    NOTE: Postgres conversations.created_at / chat_analytics.created_at 是
    TIMESTAMP WITHOUT TIME ZONE，asyncpg 拒绝把 tz-aware datetime 绑到 naive
    column。所以这里全部返回 naive datetime（UTC 时刻，但去掉 tzinfo）。
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if period == "7d":
        return now - timedelta(days=7), now - timedelta(days=14), now
    if period == "30d":
        return now - timedelta(days=30), now - timedelta(days=60), now
    # "all" – no meaningful prev period
    return datetime(2020, 1, 1), None, now


async def _count(db: AsyncSession, stmt) -> int:
    return (await db.scalar(stmt)) or 0


# ── main endpoint ────────────────────────────────────────

@router.get("")
async def get_analytics(
    period: str = Query("7d", pattern=r"^(7d|30d|all)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start, prev_start, now = _period_range(period)

    # ─── 1. Core Metrics ─────────────────────────────────

    # Total conversations
    total = await _count(db, select(func.count(Conversation.id)).where(
        Conversation.created_at >= start,
    ))
    total_prev = 0
    if prev_start:
        total_prev = await _count(db, select(func.count(Conversation.id)).where(
            and_(Conversation.created_at >= prev_start, Conversation.created_at < start),
        ))

    # AI resolution rate (from chat_analytics)
    total_a = await _count(db, select(func.count(ChatAnalytics.id)).where(
        ChatAnalytics.created_at >= start,
    ))
    answered_a = await _count(db, select(func.count(ChatAnalytics.id)).where(
        and_(ChatAnalytics.created_at >= start, ChatAnalytics.is_answered.is_(True)),
    ))
    ai_rate = round(answered_a / total_a * 100, 1) if total_a else 0.0

    ai_rate_prev = 0.0
    if prev_start:
        ta_prev = await _count(db, select(func.count(ChatAnalytics.id)).where(
            and_(ChatAnalytics.created_at >= prev_start, ChatAnalytics.created_at < start),
        ))
        aa_prev = await _count(db, select(func.count(ChatAnalytics.id)).where(
            and_(
                ChatAnalytics.created_at >= prev_start,
                ChatAnalytics.created_at < start,
                ChatAnalytics.is_answered.is_(True),
            ),
        ))
        ai_rate_prev = round(aa_prev / ta_prev * 100, 1) if ta_prev else 0.0

    # Avg response time (minutes): created_at → resolved_at
    avg_raw = await db.scalar(
        select(func.avg(extract("epoch", Conversation.resolved_at - Conversation.created_at) / 60))
        .where(and_(Conversation.resolved_at.isnot(None), Conversation.created_at >= start))
    )
    avg_resp = round(float(avg_raw), 1) if avg_raw else 0.0

    avg_resp_prev = 0.0
    if prev_start:
        avg_raw_p = await db.scalar(
            select(func.avg(extract("epoch", Conversation.resolved_at - Conversation.created_at) / 60))
            .where(and_(
                Conversation.resolved_at.isnot(None),
                Conversation.created_at >= prev_start,
                Conversation.created_at < start,
            ))
        )
        avg_resp_prev = round(float(avg_raw_p), 1) if avg_raw_p else 0.0

    # Pending teacher
    pending = await _count(db, select(func.count(Conversation.id)).where(
        Conversation.status == ConversationStatus.pending_teacher,
    ))

    # ─── 2. Daily Trends ─────────────────────────────────

    days = {"7d": 7, "30d": 30}.get(period, 90)
    trend_start = now - timedelta(days=days)

    conv_rows = await db.execute(
        select(
            func.date(Conversation.created_at).label("d"),
            func.count(Conversation.id).label("c"),
        ).where(Conversation.created_at >= trend_start)
        .group_by(text("d")).order_by(text("d"))
    )
    conv_map = {str(r.d): r.c for r in conv_rows}

    ai_rows = await db.execute(
        select(
            func.date(ChatAnalytics.created_at).label("d"),
            func.count(ChatAnalytics.id).label("c"),
        ).where(and_(ChatAnalytics.created_at >= trend_start, ChatAnalytics.is_answered.is_(True)))
        .group_by(text("d")).order_by(text("d"))
    )
    ai_map = {str(r.d): r.c for r in ai_rows}

    dates, totals, ais = [], [], []
    for i in range(days):
        d = (trend_start + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        dates.append(d)
        totals.append(conv_map.get(d, 0))
        ais.append(ai_map.get(d, 0))

    # ─── 3. AI Quality (RAG score buckets) ────────────────

    cost_row = (
        await db.execute(
            select(
                func.sum(ChatAnalytics.total_tokens).label("tokens_sum"),
                func.sum(ChatAnalytics.total_price).label("price_sum"),
                func.avg(ChatAnalytics.latency).label("latency_avg"),
            ).where(
                and_(
                    ChatAnalytics.created_at >= start,
                    ChatAnalytics.total_tokens.isnot(None),
                )
            )
        )
    ).one()

    daily_cost_rows = await db.execute(
        select(
            func.date(ChatAnalytics.created_at).label("d"),
            func.sum(ChatAnalytics.total_tokens).label("tokens"),
            func.sum(ChatAnalytics.total_price).label("price"),
        ).where(ChatAnalytics.created_at >= trend_start)
        .group_by(text("d")).order_by(text("d"))
    )
    daily_cost_map = {
        str(row.d): {"tokens": int(row.tokens or 0), "price": float(row.price or 0)}
        for row in daily_cost_rows
    }
    cost_by_day = [
        {
            "date": dates[i],
            "tokens": daily_cost_map.get(dates[i], {}).get("tokens", 0),
            "price": daily_cost_map.get(dates[i], {}).get("price", 0.0),
        }
        for i in range(len(dates))
    ]

    dist = (await db.execute(
        select(
            func.sum(case((ChatAnalytics.rag_score < 0.3, 1), else_=0)).label("low"),
            func.sum(case((and_(ChatAnalytics.rag_score >= 0.3, ChatAnalytics.rag_score < 0.6), 1), else_=0)).label("mid"),
            func.sum(case((ChatAnalytics.rag_score >= 0.6, 1), else_=0)).label("high"),
            func.count(ChatAnalytics.id).label("total"),
        ).where(and_(ChatAnalytics.created_at >= start, ChatAnalytics.rag_score.isnot(None)))
    )).one()
    hit_total = dist.total or 0
    hit_rate = round((dist.high or 0) / hit_total * 100, 1) if hit_total else 0.0

    # ─── 4. Hot Unanswered ────────────────────────────────

    hot_rows = await db.execute(
        select(
            UnansweredQuestion.id,
            UnansweredQuestion.question_text,
            UnansweredQuestion.hit_count,
        ).where(UnansweredQuestion.is_resolved.is_(False))
        .order_by(UnansweredQuestion.hit_count.desc())
        .limit(5)
    )
    hot = [{"id": r.id, "text": r.question_text, "count": r.hit_count} for r in hot_rows]

    # ─── 5. College Distribution ──────────────────────────

    college_rows = await db.execute(
        select(College.name.label("college"), func.count(Conversation.id).label("cnt"))
        .join(User, User.id == Conversation.student_id)
        .join(College, College.id == User.college_id)
        .where(Conversation.created_at >= start)
        .group_by(College.name)
        .order_by(func.count(Conversation.id).desc())
        .limit(8)
    )
    colleges = [{"name": r.college, "count": r.cnt} for r in college_rows]

    # ─── 6. Hourly Heatmap (7 × 24) ──────────────────────

    hm_rows = await db.execute(
        select(
            extract("dow", Conversation.created_at).label("dow"),
            extract("hour", Conversation.created_at).label("hr"),
            func.count(Conversation.id).label("cnt"),
        ).where(Conversation.created_at >= start)
        .group_by(text("dow"), text("hr"))
    )
    heatmap = [[0] * 24 for _ in range(7)]
    for r in hm_rows:
        heatmap[int(r.dow)][int(r.hr)] = r.cnt

    # ─── Response ─────────────────────────────────────────

    return {
        "metrics": {
            "total_questions": total,
            "total_questions_prev": total_prev,
            "ai_rate": ai_rate,
            "ai_rate_prev": ai_rate_prev,
            "avg_response_min": avg_resp,
            "avg_response_min_prev": avg_resp_prev,
            "pending_count": pending,
        },
        "trends": {
            "dates": dates,
            "total": totals,
            "ai_answered": ais,
        },
        "cost_summary": {
            "total_tokens": int(cost_row.tokens_sum or 0),
            "total_price": float(cost_row.price_sum or 0),
            "avg_latency_seconds": float(cost_row.latency_avg or 0),
            "by_day": cost_by_day,
        },
        "ai_quality": {
            "hit_rate": hit_rate,
            "score_low": dist.low or 0,
            "score_mid": dist.mid or 0,
            "score_high": dist.high or 0,
        },
        "hot_unanswered": hot,
        "college_distribution": colleges,
        "heatmap": heatmap,
    }
