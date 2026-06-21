# ISSUE-005 教师端“我的知识”不展示真实知识库

## 现象

教师端 `anjing` 登录后，“我的知识”为空，但线上业务库 `kb_entries` 有 433 条。这说明教师端看到的不是实际 Dify/KB 语料全集，而更像教师提交建议列表。

## 证据

- `GET /api/v1/knowledge/entries?pageNum=1&pageSize=50` 对 `anjing` 返回 `{"items":[],"total":0}`。
- 线上 `kb_entries` 总数为 433。
- `kb_suggestions` 只有 5 条，且都是旧 R08 验证记录。
- `kb_entries` 中 teacher draft 数量为 0，teacher review 数量为 1。

## 影响

- 老师无法知道系统已经有哪些知识。
- 老师无法判断补库是否重复、是否覆盖现有错误。
- “知识库”页面名义上是知识库，实际展示能力不完整，容易误导内测用户。

## 涉及区域

- `apps/teacher-app/src/pages/knowledge/index.vue`
- `apps/teacher-app/src/api/knowledge.ts`
- `services/gateway/app/routers/knowledge.py`
- `services/gateway/app/models/kb_entry.py`
- `services/gateway/app/models/knowledge.py`

## 建议修复方向

- 明确区分“真实知识库条目”和“教师提交/审核建议”。
- 为教师端增加 `kb_entries` 查询接口，支持按学院、分类、校区、来源搜索。
- 对 Dify 文档和业务库映射做状态展示。
- 页面命名调整为“待补问题 / 已入库知识 / 我的提交”。

