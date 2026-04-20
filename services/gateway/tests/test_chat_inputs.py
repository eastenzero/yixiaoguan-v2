"""测试 chat.py 中 build_dify_inputs 的字段构造逻辑。"""

from app.models.user import College, Class, User, UserRole
from app.routers.chat import build_dify_inputs


def test_build_dify_inputs_with_relations():
    """用户有 college 和 class_ 时，应返回人读名称。"""
    college = College(id=1, name="临床与基础医学院")
    class_ = Class(id=2, name="临床一班", college_id=1, grade_year=2023)
    user = User(
        id=1,
        staff_id="2023001",
        name="张三",
        role=UserRole.student,
        college_id=1,
        class_id=2,
        password_hash="hashed",
    )
    # 直接挂 relationship 对象（无需 session，纯内存对象即可）
    user.college = college
    user.class_ = class_

    inputs = build_dify_inputs(user)

    assert inputs == {
        "college_name": "临床与基础医学院",
        "campus": "",
        "class_id": "临床一班",
    }


def test_build_dify_inputs_with_null_relations():
    """用户未绑定 college / class_ 时，空值应转为空字符串。"""
    user = User(
        id=2,
        staff_id="2023002",
        name="李四",
        role=UserRole.student,
        college_id=None,
        class_id=None,
        password_hash="hashed",
    )
    # relationship 对象保持 None
    inputs = build_dify_inputs(user)

    assert inputs == {
        "college_name": "",
        "campus": "",
        "class_id": "",
    }


def test_build_dify_inputs_keys():
    """确认返回字典的 key 集合严格符合预期。"""
    user = User(
        id=3,
        staff_id="2023003",
        name="王五",
        role=UserRole.student,
        college_id=None,
        class_id=None,
        password_hash="hashed",
    )
    inputs = build_dify_inputs(user)
    assert set(inputs.keys()) == {"college_name", "campus", "class_id"}
    assert all(isinstance(v, str) for v in inputs.values())
