from datetime import datetime
from types import SimpleNamespace

from app.services.knowledge_service import serialize_kb_entry, summarize_knowledge_overview


def _entry(
    entry_id: int,
    *,
    freshness: str | None,
    last_verified: str | None,
    source_paths: list[str] | None = None,
    source_url: str | None = None,
    student_visible: bool = False,
    review_required: bool = False,
):
    metadata = {
        "policy_review_required": review_required,
        "sources": [{"path": path, "type": "website"} for path in source_paths or []],
    }
    if last_verified:
        metadata["last_verified"] = last_verified
    return SimpleNamespace(
        id=entry_id,
        dify_document_id=f"doc-{entry_id}",
        dify_dataset_id="dataset-main",
        title=f"资料 {entry_id}",
        content=f"正文 {entry_id}",
        raw_content=None,
        category="校园事务",
        tags=["测试"],
        original_source="正式文件",
        source_url=source_url,
        material_id=f"KB-{entry_id}",
        campus=None,
        original_filename="来源.md",
        created_at=datetime(2026, 4, 1, 8, 0, 0),
        published_at=None,
        reviewed_at=None,
        college_id=None,
        audience=["student"],
        freshness=freshness,
        governance_scope="global",
        governance_metadata=metadata,
        source_paths=source_paths,
        student_rag_visible=student_visible,
    )


def test_overview_uses_governance_verification_not_import_time():
    entries = [
        _entry(1, freshness="stable", last_verified="2026-04-16", source_paths=["a.md"], student_visible=True),
        _entry(2, freshness="current-year", last_verified="2026-04-17", source_url="https://example.test/2"),
        _entry(3, freshness="time-bound", last_verified=None, review_required=True),
        _entry(4, freshness="expired", last_verified="2026-04-15"),
    ]

    result = summarize_knowledge_overview(entries)

    assert result["total"] == 4
    assert result["verified_count"] == 3
    assert result["latest_verified_at"] == "2026-04-17"
    assert result["source_traceable_count"] == 2
    assert result["student_visible_count"] == 1
    assert result["review_required_count"] == 1
    assert result["freshness_counts"] == {
        "stable": 1,
        "current-year": 1,
        "time-bound": 1,
        "expired": 1,
    }


def test_entry_response_keeps_source_and_verification_dates_separate(monkeypatch):
    entry = _entry(5, freshness="time-bound", last_verified="2026-04-17", source_paths=["notice.md"])
    entry.governance_metadata["source_published_at"] = "2025-11-18"
    monkeypatch.setattr(
        "app.services.knowledge_service.settings.dify_global_dataset_id",
        "dataset-main",
    )

    result = serialize_kb_entry(entry)

    assert result["content"] == "正文 5"
    assert result["verified_at"] == "2026-04-17"
    assert result["source_published_at"] == "2025-11-18"
    assert result["freshness"] == "time-bound"
    assert result["effective_status"] == "time-sensitive"
    assert result["policy_level"] == "school"


def test_entry_without_governance_date_does_not_claim_import_was_verification(monkeypatch):
    entry = _entry(6, freshness=None, last_verified=None)
    monkeypatch.setattr(
        "app.services.knowledge_service.settings.dify_global_dataset_id",
        "dataset-main",
    )

    result = serialize_kb_entry(entry)

    assert result["verified_at"] is None
    assert result["source_published_at"] is None
    assert result["freshness"] == "unclassified"
