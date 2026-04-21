---
id: "r08-5-exec-admin-review"
parent: "R08-5"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "medium"
foundation: false

scope:
  - "services/gateway/app/routers/knowledge.py"
  - "services/gateway/app/schemas/knowledge.py"
  - "services/gateway/app/services/knowledge_service.py"
  - "services/gateway/tests/test_knowledge_admin_review.py"
  - "apps/teacher-app/src/pages/knowledge/index.vue"
  - "apps/teacher-app/src/api/knowledge.ts"
  - ".tasks/reports/r08-5-exec-admin-review_report.md"

out_of_scope:
  - "学生端任何页面"
  - "新的 admin-app"
  - "复杂审核流（多级审批 / 审批历史追踪）"
  - "批量审核"

context_files:
  - "docs/requirements/R08-教师-KB-运营闭环.md"
  - ".tasks/r08-4-exec-polish-draft-publish.md"
  - "apps/teacher-app/src/pages/knowledge/index.vue"
  - "services/gateway/app/models/knowledge.py"
  - "services/gateway/app/services/knowledge_service.py"

done_criteria:
  L0: "管理员可查看 global 待审核知识列表，并执行通过/驳回；通过后才真正发 Dify 并写入 kb_entries；驳回后保留 reject_reason"
  L1: "pytest services/gateway/tests/test_knowledge_admin_review.py 通过；覆盖仅管理员可审 / approve 成功 / reject 成功 / 重复审核拒绝"
  L2: "165 联调：管理员登录后在统一 teacher-app 知识页看到待审核条目；approve 后 Dify 新增文档；reject 后教师端能看到驳回状态或原因"
  L3: "审核链不影响 class/college 直发路径；已有直发链路保持可用"

depends_on:
  - "r08-4-exec-polish-draft-publish"
  - "r08-3-exec-teacher-kb-workbench"
created_at: "2026-04-21"
---

# R08-5 Executor · 管理员审核链路

> **目标状态**：`scope=global` 的知识条目必须经过管理员审核后才发布。管理员与教师复用同一 teacher-app 页面体系，不新开独立后台。

## 背景

R03 已确认“知识审核由管理员负责”，R08 对其做了细化：

- `class` / `college`：教师直发
- `global`：管理员审核

R08-4 已负责把 `global` 提交沉淀为 `pending` 草稿；R08-5 只需要把这条链闭合。

## 必读上下文

1. `docs/requirements/R03-开发前确认事项.md`
2. `docs/requirements/R08-教师-KB-运营闭环.md`
3. `.tasks/r08-4-exec-polish-draft-publish.md`
4. `apps/teacher-app/src/pages/knowledge/index.vue`
5. `services/gateway/app/services/knowledge_service.py`

## 执行重点

### 1. 后端接口

至少补齐：

```http
GET  /api/v1/knowledge/review/pending?limit=20
POST /api/v1/knowledge/review/{id}/approve
POST /api/v1/knowledge/review/{id}/reject
```

约束：

- 只有管理员可调用
- 仅 `status=pending` 的条目可审核
- `approve`：真正调用 Dify 发布，并转为 `approved`
- `reject`：转为 `rejected`，保留 `reject_reason`

### 2. 前端最小审核 UI

管理员登录 teacher-app 后：

- 在知识页看到 `待审核` tab
- 每条待审核卡片至少显示：
  - 标题 / representative_query
  - 提交教师（若有）
  - scope=global 标识
  - 两个按钮：`通过` / `驳回`

驳回时允许填一个简短原因；若不填，后端可兜底 `管理员驳回`。

### 3. 审核后反馈

- 通过：toast `审核通过，已发布`
- 驳回：toast `已驳回`
- 审核完成后，从待审核列表移除
- 教师在“我的知识”里能看到最新状态

### 4. 一致性要求

- `approve` 失败时不能出现“前端显示已通过、后端没发成功”的假状态
- `reject` 不应创建 `KbEntry`
- 已审核条目再次审核要返回 400

## 测试策略

`tests/test_knowledge_admin_review.py` 至少覆盖：

1. 教师访问审核接口 403
2. 管理员获取待审核列表成功
3. approve 把 pending 变 approved，并触发发布
4. reject 把 pending 变 rejected，并保留 reason
5. 重复 approve / reject 被拒绝

## 已知陷阱

- 不要让管理员审核列表混入 class/college 直发条目
- 不要在前端本地推断“审核成功”，一定要以后端返回为准
- 不要新增第二套 admin 路由前缀；沿用 `/api/v1/knowledge/*`

## 报告应包含

1. 审核接口清单
2. 管理员 UI 截图
3. approve / reject 各 1 条真实联调结果
4. 驳回原因在教师侧的回显方式
5. 重复审核保护说明

## 回滚方案

- 恢复审核路由与前端按钮
- 不影响已存在 teacher 直发链路
- 已发布到 Dify 的测试条目可手工删除
