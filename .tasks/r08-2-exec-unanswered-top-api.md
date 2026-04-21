---
id: "r08-2-exec-unanswered-top-api"
parent: "R08-2"
type: "feature"
status: "pending"
tier: "T3"
priority: "high"
risk: "medium"
foundation: true

scope:
  - "services/gateway/app/routers/knowledge.py"
  - "services/gateway/app/schemas/knowledge.py"
  - "services/gateway/app/services/knowledge_service.py"
  - "services/gateway/tests/test_knowledge_unanswered_top.py"
  - ".tasks/reports/r08-2-exec-unanswered-top-api_report.md"

out_of_scope:
  - "services/gateway/app/routers/chat.py"
  - "services/gateway/app/services/dify_client.py"
  - "apps/**"
  - "教师答复提交 / AI 润色 / 发布逻辑"
  - "管理员审核 UI"

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R08-教师-KB-运营闭环.md"
  - ".tasks/r08-1-exec-analytics-capture.md"
  - "services/gateway/app/models/knowledge.py"
  - "services/gateway/app/models/user.py"
  - "services/gateway/app/routers/auth.py"

done_criteria:
  L0: "提供教师/管理员可访问的 Top N 高频待补问题 API；默认按 hit_count DESC、last_seen_at DESC 排序；教师只能看到本学院（允许 null 兜底）的待补问题，管理员可看全局"
  L1: "pytest services/gateway/tests/test_knowledge_unanswered_top.py 通过；覆盖教师视角 / 管理员视角 / 已解决过滤 / limit 生效 / 越权拒绝"
  L2: "165 远端能用教师 token 调 GET /api/v1/knowledge/unanswered-top?limit=10 拿到稳定 JSON；字段至少含 id / question_text / hit_count / latest_at / sample_conv_ids"
  L3: "在真实库里验证：同类问题多次追问后 hit_count 累加，已被 R08-4/5 产出知识的条目不再出现在待补列表中"

depends_on:
  - "r08-1-exec-analytics-capture"
created_at: "2026-04-21"
---

# R08-2 Executor · Top N 高频待补问题 API

> **目标状态**：把 R08-1 采集到的原始 analytics 数据，收敛成教师可直接操作的“高频待补问题列表”。本任务只做**统计层 + API 层**，不碰前端展示、不碰教师答复提交。

## 背景

R08-1 已经负责把学生经 `/api/chat/send` 打到 AI 的问答轨迹，异步落到 `chat_analytics`；同时对 `is_answered=false` 的 query 做聚合沉淀（`unanswered_questions`）。R08-2 的职责不是重新发明聚类算法，而是把这份沉淀过的数据**稳定、可分页、带权限地暴露出来**，供 R08-3 教师端工作台直接消费。

## 必读上下文

1. `docs/requirements/R08-教师-KB-运营闭环.md` § 四 / R08-2
2. `.tasks/r08-1-exec-analytics-capture.md`
3. `services/gateway/app/models/knowledge.py` 中 `UnansweredQuestion`
4. `services/gateway/app/models/user.py`（学院/班级与角色边界）
5. `services/gateway/app/utils/deps.py`（JWT + 当前用户）

## 执行重点

### 1. API 契约

新增（或补齐）以下只读接口：

```http
GET /api/v1/knowledge/unanswered-top?limit=20
Authorization: Bearer <teacher_or_admin_token>
```

返回：

```json
{
  "items": [
    {
      "id": 12,
      "question_text": "宿舍电费怎么交",
      "hit_count": 7,
      "latest_at": "2026-04-21T10:33:00",
      "college_id": 1,
      "class_id": null,
      "sample_conv_ids": [88, 71, 65]
    }
  ],
  "total": 1
}
```

### 2. 权限与可见性

- **教师**：只能看到自己学院范围内的待补问题
- **管理员**：可看全局
- **学生**：403
- 对 `college_id is null` 的历史脏数据，可允许教师看到（避免漏掉“未绑定学院但真实应该归属本院”的旧记录）；但**不要**让教师看到明确属于其他学院的数据

### 3. 排序与过滤

固定规则：

1. `is_resolved = false`
2. `ORDER BY hit_count DESC, last_seen_at DESC, id DESC`
3. `limit` 取值 `[1, 100]`

本任务**不要**引入新的搜索、筛选、分页复杂度；教师端第一页只需要 Top N。

### 4. 不变式

- API 只消费已沉淀的 `UnansweredQuestion`，**不直接扫描** `chat_analytics` 做实时聚类
- 不要在本任务重写 `query_norm` 算法
- 不要把“是否已解决”的判定交给前端，后端返回前就要过滤干净

## 测试策略

`tests/test_knowledge_unanswered_top.py` 至少覆盖：

1. 教师只能看本学院待补问题
2. 管理员能看跨学院待补问题
3. `is_resolved=true` 的记录不会返回
4. `limit=1` 生效
5. 学生访问返回 403

测试风格与 R07 现有单测一致，优先路由/服务层单测，不要求启动完整 HTTP server。

## 已知陷阱

- 不要把“聚类统计”实现成每次 GET 都扫 `chat_analytics`
- 不要在返回体里暴露学生敏感信息
- `sample_conv_ids` 仅用于教师后续定位样本会话，不需要额外 join conversations
- 若真实库中存在旧数据缺 `last_seen_at`，应在 migration/backfill 层解决，不要在 API 层硬补

## 报告应包含

1. 最终接口路径与 response 示例
2. 教师/管理员权限边界说明
3. 排序字段与 SQL/ORM 片段
4. 165 远端真实调用结果截图或 curl 输出
5. 与 R08-3 的前端联调注意事项

## 回滚方案

- 回滚本任务新增路由/服务/测试
- 不涉及数据删除
- 不影响学生问答主链
