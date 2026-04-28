REFUSAL_KEYWORDS = [
    "尚未学习到",
    "请咨询您的辅导员",
    "无法回答",
    "暂时无法",
    "超出了我的知识范围",
    "建议您直接咨询",
    "暂时不可用",
    "请稍后重试",
    "无法为您提供",
    "没有找到相关",
    "不在我的服务范围",
    "转人工请求",
    "转接人工客服",
    "转人工服务",
    "转接人工",
    "无法理解",
    "请联系",
    "建议您联系",
    "建议咨询",
    "我没有相关信息",
    "我无法确认",
    "建议直接联系",
]


def is_refusal(answer: str, sources: list | None = None) -> bool:
    """Detect if Dify reply is a refusal / out-of-scope answer."""
    if not answer:
        return True
    for kw in REFUSAL_KEYWORDS:
        if kw in answer:
            return True
    if answer.startswith("抱歉") and not sources:
        return True
    if len(answer.strip()) < 8 and not sources:
        return True
    return False
