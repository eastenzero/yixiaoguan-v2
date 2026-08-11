from types import SimpleNamespace

from app.services.source_evidence import (
    ANSWER_DISCLAIMER,
    build_source_item,
    classify_source,
    filter_for_college,
    sort_sources,
)


def test_school_and_college_official_domains_are_verified():
    assert classify_source(
        "https://sa.sdfmu.edu.cn/info/1.htm", {}
    ) == ("official_web", "学校官网", True)
    assert classify_source(
        "https://mm.sdfmu.edu.cn/info/2.htm", {"authority_level": "college"}
    ) == ("official_web", "学院官网", True)


def test_wechat_requires_account_verification():
    url = "https://mp.weixin.qq.com/s/example"
    assert classify_source(url, {}) == (
        "wechat_pending",
        "公众号原文·主体待核验",
        False,
    )
    assert classify_source(url, {"verified_official_account": True}) == (
        "official_wechat",
        "已核验公众号",
        True,
    )


def test_source_item_keeps_evidence_metadata_and_longer_excerpt():
    resource = {
        "document_id": "doc-1",
        "dataset_id": "dataset-1",
        "document_name": "奖学金评审通知",
        "score": 0.92,
        "content": "正文" * 400,
        "metadata": {
            "source_url": "https://mm.sdfmu.edu.cn/info/1.htm",
            "authority_level": "college",
            "college": "医药管理学院",
            "published_at": "2025-10-11",
            "academic_year": "2024-2025",
            "effective_status": "historical",
            "screenshot_url": "/static/evidence/example.png",
        },
    }
    entry = SimpleNamespace(
        dify_document_id="doc-1",
        dify_dataset_id="dataset-1",
        title="fallback",
        source_url=None,
        original_source="原文件.md",
        category="奖助学金",
        campus="泰安校区",
        freshness="time-bound",
        source_paths=["W2/奖助学金/通知.md"],
        governance_metadata={"last_verified": "2026-04-17"},
    )
    item = build_source_item(resource, entry)
    assert item["college"] == "医药管理学院"
    assert item["source_label"] == "学院官网"
    assert item["verified"] is True
    assert item["effective_status"] == "historical"
    assert item["last_verified"] == "2026-04-17"
    assert item["source_paths"] == ["W2/奖助学金/通知.md"]
    assert len(item["content"]) == 600


def test_sources_are_sorted_by_date_then_authority():
    sources = [
        {"published_at": "2024-09-24", "source_type": "official_web", "score": 0.9},
        {"published_at": "2025-10-11", "source_type": "knowledge_base", "score": 0.8},
        {"published_at": "2025-10-11", "source_type": "official_web", "score": 0.7},
    ]
    ordered = sort_sources(sources)
    assert ordered[0]["source_type"] == "official_web"
    assert ordered[-1]["published_at"] == "2024-09-24"


def test_college_filter_never_borrows_another_colleges_notice():
    sources = [
        {"title": "校级制度", "college": "全校"},
        {"title": "药学院公示", "college": "药学院（药物研究所）"},
        {"title": "管院公示", "college": "医药管理学院"},
        {"title": "旧资料未标学院", "college": None},
    ]
    filtered = filter_for_college(sources, "医药管理学院")
    assert [source["title"] for source in filtered] == [
        "校级制度",
        "管院公示",
        "旧资料未标学院",
    ]


def test_disclaimer_is_precise_and_non_authoritative():
    assert "仅供办事参考" in ANSWER_DISCLAIMER
    assert "不构成" in ANSWER_DISCLAIMER
    assert "当年度正式通知" in ANSWER_DISCLAIMER
