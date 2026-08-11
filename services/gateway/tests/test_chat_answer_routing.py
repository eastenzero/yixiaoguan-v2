from app.routers.chat import (
    _is_scholarship_overview_query,
    _is_scholarship_query,
    add_curated_library_sources,
    add_curated_scholarship_sources,
    build_dify_query,
)
from app.services.dify_client import filter_actionable_suggestions


def test_every_knowledge_answer_uses_answer_first_structure():
    routed = build_dify_query("校园卡丢了怎么办？")

    assert "统一回答方式" in routed
    assert "开头用2—4句话直接回答" in routed
    assert "不得把已知结论藏在保守声明后面" in routed
    assert "不输出‘知识库尚未接入’" in routed


def test_scholarship_overview_injects_layered_answer_structure():
    routed = build_dify_query("我们学校有哪些奖学金？")

    assert "一、国家级" in routed
    assert "二、山东省级" in routed
    assert "三、山一大校级" in routed
    assert "四、学院/社会专项" in routed
    assert "不得先要求用户补充年级或学院" in routed
    assert "每个层级先用1个独立段落" in routed
    assert "特别优秀奖励’和‘家庭经济困难学生励志奖励" in routed
    assert "特定地区少数民族学生专项励志奖励" in routed
    assert "学业与综测表现、突出成果、自强成长及新生" in routed
    assert "10,000元" in routed
    assert "国家励志奖学金：二年级及以上，现行每生每年6,000元" in routed
    assert "山东省政府奖学金：二年级及以上，每生每年6,000元" in routed
    assert "山东省政府励志奖学金：每生每年5,000元" in routed
    assert "一等1,500元" in routed
    assert "4,000元，全校每学年不超过50名" in routed
    assert "不得自动延续为新学年标准" in routed


def test_scholarship_noun_queries_force_a_complete_overview():
    for question in (
        "奖学金",
        "奖学金有哪些？",
        "我们学校有哪些奖学金？",
        "奖学金政策介绍",
        "奖学金分类",
    ):
        assert _is_scholarship_overview_query(question)
        routed = build_dify_query(question)
        assert "本题已判定为奖学金总览" in routed
        assert "必须直接输出一篇完整综述" in routed
        assert "国家级、山东省政府级、山一大校级、学院及社会专项" in routed

    assert not _is_scholarship_overview_query("弘毅奖学金需要什么条件？")


def test_scholarship_and_failed_course_keep_both_contexts():
    routed = build_dify_query("挂科会影响奖学金吗？", "2024级1班")

    assert "奖学金分层事实与输出顺序" in routed
    assert "2024级及以后" in routed
    assert "直接按规定重修" in routed


def test_scholarship_aliases_share_the_same_school_specific_answer_route():
    questions = (
        "国奖怎么评？",
        "省政府奖有哪些？",
        "弘毅需要什么条件？",
        "自强之星怎么申请？",
        "挂科影响评奖评优吗？",
        "济南奖谁能报？",
    )

    for question in questions:
        assert _is_scholarship_query(question)
        routed = build_dify_query(question)
        assert "奖学金分层事实与输出顺序" in routed
        assert "校级综合奖学金" in routed
        assert "‘弘毅’奖学金" in routed
        sources = add_curated_scholarship_sources([], question)
        assert len(sources) >= 5

    assert any(
        source.get("source_url") == "https://sa.sdfmu.edu.cn/info/1341/18451.htm"
        for source in add_curated_scholarship_sources([], "自强之星怎么申请？")
    )
    assert any(
        source.get("source_url") == "https://sa.sdfmu.edu.cn/info/1341/21001.htm"
        for source in add_curated_scholarship_sources([], "济南奖谁能报？")
    )

    assert not _is_scholarship_query("国家助学贷款怎么办？")


def test_suggestions_drop_profile_requests_but_keep_answerable_questions():
    questions = filter_actionable_suggestions([
        "请提供你的学院和年级",
        "国家奖学金和国家励志奖学金有什么区别？",
        "请补充你的职位",
        "挂科会影响评选吗？",
    ])

    assert questions == [
        "国家奖学金和国家励志奖学金有什么区别？",
        "挂科会影响评选吗？",
    ]


def test_library_hours_include_both_campuses_and_full_day_opening():
    routed = build_dify_query("两个校区图书馆几点开门？")

    assert "济南校区和泰安校区" in routed
    assert "07:00" in routed
    assert "22:00" in routed
    assert "下午正常开放" in routed


def test_library_hours_cover_common_student_phrasings():
    for question in (
        "图书馆周末开吗？",
        "图书馆下午能进吗？",
        "图书馆晚上什么时候关门？",
        "图书馆今天能去自习吗？",
    ):
        routed = build_dify_query(question)
        assert "07:00开放、22:00闭馆" in routed
        assert "周末也正常开放" in routed


def test_library_hours_append_operational_and_official_materials():
    sources = add_curated_library_sources([], "图书馆周末开吗？")

    assert sources[0]["title"] == "两校区图书馆日常开放时间（07:00—22:00）"
    assert sources[1]["source_url"] == "https://www.sdfmu.edu.cn/info/1076/12216.htm"
    assert sources[2]["source_url"] == "https://www.sdfmu.edu.cn/index/xysh/qjxy.htm"


def test_scholarship_answers_append_national_provincial_and_school_sources():
    sources = add_curated_scholarship_sources([], "我们学校有哪些奖学金？")

    assert len(sources) == 5
    assert sources[0]["source_label"] == "中国政府网"
    assert sources[1]["source_label"] == "财政部官网"
    assert sources[2]["source_label"] == "山东省政策文件"
    assert sources[3]["source_url"] == "https://sa.sdfmu.edu.cn/info/1341/21131.htm"
    assert sources[4]["source_url"] == "https://sa.sdfmu.edu.cn/info/1341/21411.htm"
