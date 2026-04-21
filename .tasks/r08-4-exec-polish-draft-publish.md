---
id: "r08-4-exec-polish-draft-publish"
parent: "R08-4"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "high"
foundation: true

scope:
  - "services/gateway/alembic/versions/xxxx_r08_scope_publish.py"
  - "services/gateway/app/models/knowledge.py"
  - "services/gateway/app/schemas/knowledge.py"
  - "services/gateway/app/services/dify_client.py"
  - "services/gateway/app/services/knowledge_service.py"
  - "services/gateway/app/routers/knowledge.py"
  - "services/gateway/tests/test_knowledge_draft_publish.py"
  - ".tasks/reports/r08-4-exec-polish-draft-publish_report.md"

out_of_scope:
  - "apps/**"
  - "管理员审核按钮与前端审核页"
  - "Dify 数据集运维脚本"
  - "旧知识批量迁移"

context_files:
  - "docs/requirements/R08-教师-KB-运营闭环.md"
  - "services/gateway/app/models/kb_entry.py"
  - "services/gateway/app/models/knowledge.py"
  - "services/gateway/app/services/dify_client.py"
  - "services/gateway/app/config.py"
  - "services/gateway/alembic/versions/ff1f0ab0c5f8_add_kb_entries_table.py"

done_criteria:
  L0: "教师调用提交接口后，系统能把 raw_answer 润色为可发布 KB 内容，并按 scope 执行：class/college 直接发布到 Dify 并写入 kb_entries；global 生成待审核草稿，不直接发 Dify"
  L1: "pytest services/gateway/tests/test_knowledge_draft_publish.py 通过；覆盖 class 直发 / college 直发 / global 待审 / Dify 失败回滚 / 越权 scope 拒绝"
  L2: "165 联调：教师用学院范围提交一条知识后，PG 中 `kb_suggestions` / `kb_entries` 均可见记录，且 Dify 对应 dataset 中出现新文档；global 提交后仅 `kb_suggestions.status=pending`"
  L3: "流程具备降级能力：即使 Dify polish key 未配置，也能以规则化模板生成内容，不阻塞教师提交"

depends_on:
  - "r08-2-exec-unanswered-top-api"
created_at: "2026-04-21"
---

# R08-4 Executor · AI 润色 + 草稿存储 + 直发发布

> **目标状态**：教师提交原始答复后，后端能把它整理为 KB 条目，并根据 scope 决定是“直接发布”还是“进入待审”。本任务是 R08 主链里最核心的一段后端能力。

## 背景

项目里已有这些可复用基础：

- `KbSuggestion`：可作为“草稿/建议条目”载体
- `CollegeDataset`：学院到 Dify dataset 的映射
- `KbEntry`：已发布文档与 Dify 文档 ID 的映射
- `dify_client.create_document()`：已有 Dify Dataset API 调用

因此本任务**优先复用旧模型**，只给 `KbSuggestion` 补 R08 需要的 scope / representative_query / reject_reason / published_at 等字段，不新起一套重复的 `kb_drafts` 体系，除非执行人确认旧模型无法承载。

## 必读上下文

1. `docs/requirements/R08-教师-KB-运营闭环.md` § R08-4 / R08-5
2. `services/gateway/app/models/knowledge.py`
3. `services/gateway/app/models/kb_entry.py`
4. `services/gateway/app/services/dify_client.py`
5. `services/gateway/app/config.py`

## 执行重点

### 1. 数据模型扩展

`KbSuggestion` 至少补齐：

- `scope: class | college | global`
- `scope_value: int | null`
- `representative_query: text`
- `question_hash: varchar(64)`
- `reject_reason: text | null`
- `published_at: datetime | null`

必要时给 `UnansweredQuestion` 补：

- `class_id`
- `last_seen_at`

### 2. 提交接口

```http
POST /api/v1/knowledge/drafts
Authorization: Bearer <teacher_or_admin_token>
Content-Type: application/json

{
  "unanswered_question_id": 12,
  "raw_answer": "宿舍电费可在校园生活服务平台缴纳……",
  "scope": "college",
  "scope_value": 1
}
```

返回：

```json
{
  "entry": { ... },
  "publish_mode": "published"
}
```

其中 `publish_mode` 只能是：

- `published`
- `pending_review`

### 3. scope 规则（必须严格执行）

- `class`：教师只能发到自己班级；成功后直接发布
- `college`：教师只能发到自己学院；成功后直接发布
- `global`：教师可提交，但只能进入 `pending`，**不得直接发 Dify**
- 管理员后续在 R08-5 审核通过后，才真正发布 `global`

### 4. AI 润色策略

优先调用 Dify / polish app，把教师 `raw_answer` 整理成 KB 文本。

但要有**硬降级兜底**：

- 若未配置 `dify_polish_api_key`
- 或 Dify polish 请求失败

则用本地模板产出：

```text
适用范围：xx

问题：xx

答复：xx
```

**重点**：不能因为 AI 润色失败就让教师提交失败。

### 5. Dify 发布与事务边界

- class/college 直发时：
  1. 选定 dataset
  2. `create_document`
  3. 写 `KbEntry`
  4. 更新 `KbSuggestion.status=approved`
- 若 Dify 创建文档失败：
  - 当前请求返回失败
  - DB 不应留下“已发布”假状态

### 6. 未回答问题联动

若本次提交来自 `unanswered_question_id`：

- 直发成功 → 对应 `UnansweredQuestion.is_resolved = true`
- global 待审 → 可先挂 `kb_suggestion_id`，但不要标 resolved，避免教师列表过早消失；或者按父文档最终定义执行，但报告里必须写清楚

> 推荐：**仅审核通过/直发成功后** 才真正 `is_resolved=true`，语义更稳。

## 测试策略

至少覆盖：

1. `class` scope 直发成功
2. `college` scope 直发成功
3. `global` scope 进入 pending
4. 教师试图提交他院/他班 scope 被拒绝
5. Dify `create_document` 抛错时状态不假成功
6. polish 失败时 fallback 模板仍能提交

## 已知陷阱

- 不要把 `global` 也直发到 `dify_global_dataset_id`
- 不要让教师自定义任意 `scope_value`
- 不要在 DB commit 之后再补 `KbEntry`，否则失败会造成双写不一致
- 若复用 `KbSuggestion`，报告里必须解释为什么没有新建 `kb_drafts`

## 报告应包含

1. 最终采用“复用旧模型”还是“新建草稿表”，以及理由
2. scope 权限检查逻辑
3. Dify dataset 选择策略
4. AI polish 失败降级策略
5. 165 上真实提交 1 条 college + 1 条 global 的结果

## 回滚方案

- 回滚 migration
- 回滚 knowledge router/service 改动
- 对测试环境中新建的 Dify 文档可手工删除
