"""测试 chat.py 中 build_dify_inputs 的字段构造逻辑（R04-N1）。"""

from types import SimpleNamespace
from app.routers.chat import build_dify_inputs


def test_build_dify_inputs_with_all_relations():
    """用户有 college（含 campus）和 class_ 时，应返回人读名称。"""
    college = SimpleNamespace(name="医学信息工程学院", campus="主校区")
    class_ = SimpleNamespace(name="2024级1班")
    user = SimpleNamespace(college=college, class_=class_)

    inputs = build_dify_inputs(user)

    assert inputs == {
        "college_name": "医学信息工程学院",
        "campus": "主校区",
        "class_name": "2024级1班",
    }


def test_build_dify_inputs_with_no_college():
    """用户未绑定 college / class_ 时，空值应转为空字符串。"""
    user = SimpleNamespace(college=None, class_=None)

    inputs = build_dify_inputs(user)

    assert inputs == {
        "college_name": "",
        "campus": "",
        "class_name": "",
    }


def test_build_dify_inputs_college_no_class():
    """用户有 college 但无 class_ 时，class_name 应为空字符串。"""
    college = SimpleNamespace(name="护理学院", campus="")
    user = SimpleNamespace(college=college, class_=None)

    inputs = build_dify_inputs(user)

    assert inputs["class_name"] == ""
    assert inputs["college_name"] == "护理学院"
    assert inputs["campus"] == ""


def test_build_dify_inputs_keys():
    """确认返回字典的 key 集合严格符合预期。"""
    user = SimpleNamespace(college=None, class_=None)
    inputs = build_dify_inputs(user)
    assert set(inputs.keys()) == {"college_name", "campus", "class_name"}
    assert all(isinstance(v, str) for v in inputs.values())
