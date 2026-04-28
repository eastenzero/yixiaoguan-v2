from app.services.refusal import is_refusal


def test_plain_answer_with_sources_is_not_refusal():
    assert is_refusal("这是根据资料整理的完整回答。", [{"title": "source"}]) is False


def test_keyword_answer_is_refusal():
    assert is_refusal("我尚未学习到这个问题的答案。", [{"title": "source"}]) is True


def test_sorry_without_sources_is_refusal():
    assert is_refusal("抱歉，我暂时不能回答。") is True


def test_sorry_with_sources_is_not_refusal():
    assert is_refusal("抱歉，这里需要更准确地说。", [{"title": "source"}]) is False


def test_empty_answer_is_refusal():
    assert is_refusal("") is True


def test_very_short_answer_without_sources_is_refusal():
    assert is_refusal("不知道") is True


def test_new_keyword_answer_is_refusal():
    assert is_refusal("我无法确认这个信息。", [{"title": "source"}]) is True
