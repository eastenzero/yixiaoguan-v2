# ISSUE-003 高频待补队列被非知识问题污染

## 现象

教师端“高频待补”列表中混入大量不适合入库的问题，例如寒暄、情绪表达、转人工、反馈投诉和无意义短句。

## 证据

线上 `unanswered_questions` 有 26 条，全部 unresolved。教师端可见的高频待补包括：

- `我想回家`
- `联系导员`
- `你好`
- `我想谈恋爱`
- `我不要`
- `我想转人工`
- `hello`
- `没有`
- `呼叫老师`
- `我有点郁闷`
- `这个你做的不对，不能骗我`

## 影响

- 老师打开知识库会看到大量“不能入库”的内容，运营压力大。
- 真正应该补充的制度、流程、地点、联系方式类问题被噪声淹没。
- 如果老师误补，Dify 知识库会继续被污染。

## 涉及区域

- `services/gateway/app/services/analytics.py`
- `services/gateway/app/services/refusal.py`
- `services/gateway/app/routers/chat.py`
- `apps/teacher-app/src/pages/knowledge/index.vue`

## 建议修复方向

- 在写入 `unanswered_questions` 前增加意图分类。
- 过滤或分流：寒暄、情绪支持、转人工、投诉反馈、无意义短句、医疗用药类高风险问题。
- 教师端增加“忽略/归档/合并/标记非知识问题”。
- 待补队列展示分类、来源会话、最近样例和低置信原因。

