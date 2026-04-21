import logging
from hashlib import sha256
import re
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_analytics import ChatAnalytics
from app.models.knowledge import UnansweredQuestion
from app.models.user import User

try:
    import jieba  # type: ignore[import-not-found]
except ImportError:
    class _JiebaFallback:
        @staticmethod
        def initialize() -> None:
            return None

        @staticmethod
        def cut(text: str):
            return [text]

    jieba = _JiebaFallback()

logger = logging.getLogger(__name__)

jieba.initialize()

STOPWORDS = {
    "的",
    "了",
    "吗",
    "呢",
    "呀",
    "啊",
    "请问",
    "一下",
    "一下子",
    "我",
    "想",
    "要",
    "这个",
    "那个",
    "怎么",
    "如何",
    "一下哈",
}
PUNCTUATION_PATTERN = re.compile(r"[\s\W_]+", re.UNICODE)
SYNONYM_REPLACEMENTS = {
    "缴纳": "交",
    "缴费": "交费",
    "缴": "交",
}


def normalize_query(raw: str) -> str | None:
    normalized = raw.strip().lower()
    for source, target in SYNONYM_REPLACEMENTS.items():
        normalized = normalized.replace(source, target)
    normalized = PUNCTUATION_PATTERN.sub(" ", normalized).strip()
    if not normalized:
        return None

    tokens = [token.strip() for token in jieba.cut(normalized) if token.strip()]
    filtered_tokens = [token for token in tokens if token not in STOPWORDS and not token.isdigit()]
    if not filtered_tokens:
        filtered_tokens = [token for token in tokens if not token.isdigit()]
    if not filtered_tokens:
        return None

    unique_tokens: list[str] = []
    for token in filtered_tokens:
        if token not in unique_tokens:
            unique_tokens.append(token)

    if not unique_tokens:
        return None
    return "|".join(sorted(unique_tokens)[:3])[:255]


def _iter_resources(metadata: dict) -> Iterable[dict]:
    retriever_resources = metadata.get("retriever_resources")
    if isinstance(retriever_resources, list):
        return retriever_resources

    retrieval_result = metadata.get("retrieval_result")
    if isinstance(retrieval_result, list):
        return retrieval_result
    if isinstance(retrieval_result, dict):
        records = retrieval_result.get("records")
        if isinstance(records, list):
            return records

    return []


def extract_rag_metrics(metadata: dict | None) -> tuple[float | None, str | None]:
    if not isinstance(metadata, dict):
        return None, None

    best_score: float | None = None
    best_doc_name: str | None = None
    for resource in _iter_resources(metadata):
        if not isinstance(resource, dict):
            continue
        raw_score = resource.get("score")
        if not isinstance(raw_score, (int, float, str)):
            continue
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        if best_score is None or score > best_score:
            best_score = score
            best_doc_name = (
                resource.get("document_name")
                or resource.get("document_title")
                or resource.get("name")
            )
    return best_score, best_doc_name


def judge_is_answered(
    rag_score: float | None,
    response_text: str,
    *,
    score_threshold: float = 0.3,
    min_answer_length: int = 20,
) -> bool:
    if rag_score is None:
        return False
    if rag_score is not None and rag_score >= score_threshold:
        return True
    return len(response_text.strip()) >= min_answer_length


def build_question_hash(raw_query: str, query_norm: str | None) -> str:
    fingerprint = query_norm or raw_query.strip().lower()
    return sha256(fingerprint.encode("utf-8")).hexdigest()


async def upsert_unanswered_question(
    db: AsyncSession,
    *,
    conv_id: int,
    user: User,
    raw_query: str,
    query_norm: str | None,
) -> None:
    question_hash = build_question_hash(raw_query, query_norm)
    result = await db.execute(
        select(UnansweredQuestion).where(UnansweredQuestion.question_hash == question_hash)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.hit_count += 1
        sample_conv_ids = list(existing.sample_conv_ids or [])
        if conv_id not in sample_conv_ids:
            sample_conv_ids.append(conv_id)
        existing.sample_conv_ids = sample_conv_ids[:10]
        if existing.college_id is None:
            existing.college_id = user.college_id
        return

    db.add(
        UnansweredQuestion(
            question_text=raw_query,
            question_hash=question_hash,
            hit_count=1,
            sample_conv_ids=[conv_id],
            college_id=user.college_id,
            is_resolved=False,
        )
    )


async def record_chat_analytics(
    db: AsyncSession,
    *,
    conv_id: int,
    user: User,
    raw_query: str,
    response_text: str,
    dify_metadata: dict | None,
) -> None:
    try:
        rag_score, kb_doc_matched = extract_rag_metrics(dify_metadata)
        query_norm = normalize_query(raw_query)
        is_answered = judge_is_answered(rag_score, response_text)
        analytics = ChatAnalytics(
            conversation_id=conv_id,
            user_id=user.id,
            user_college_id=user.college_id,
            user_class_id=user.class_id,
            user_query=raw_query,
            query_norm=query_norm,
            rag_score=rag_score,
            kb_doc_matched=kb_doc_matched,
            is_answered=is_answered,
        )
        db.add(analytics)
        if not is_answered:
            await upsert_unanswered_question(
                db,
                conv_id=conv_id,
                user=user,
                raw_query=raw_query,
                query_norm=query_norm,
            )
        await db.commit()
    except Exception as exc:
        logger.warning("Failed to record chat analytics for conv=%s user=%s: %s", conv_id, user.id, exc)
        await db.rollback()
