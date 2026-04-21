# R08-5 Executor Report · 管理员审核链路

## 改动文件

- `services/gateway/app/routers/knowledge.py`
- `services/gateway/app/schemas/knowledge.py`
- `services/gateway/app/services/knowledge_service.py`
- `services/gateway/tests/test_knowledge_admin_review.py`
- `apps/teacher-app/src/pages/knowledge/index.vue`
- `apps/teacher-app/src/api/knowledge.ts`
- `.tasks/reports/r08-5-exec-admin-review_report.md`

## 审核接口清单

已实现：

- `GET /api/v1/knowledge/reviews/pending?limit=20`
- `POST /api/v1/knowledge/reviews/{id}/approve`
- `POST /api/v1/knowledge/reviews/{id}/reject`

并补了兼容别名：

- `GET /api/v1/knowledge/review/pending`
- `POST /api/v1/knowledge/review/{id}/approve`
- `POST /api/v1/knowledge/review/{id}/reject`

## 核心实现

### 1. 待审核列表

只返回：

- `scope = global`
- `status = pending`

排序：

- `created_at DESC`
- `id DESC`

只有管理员可调用。

### 2. approve 语义

管理员 approve 时：

- 校验当前条目仍为 `pending`
- 调 Dify 真正发布
- 写入 `kb_entries`
- `KbSuggestion.status -> approved`
- 回填：
  - `reviewed_by`
  - `reviewed_at`
  - `published_at`
  - `dify_document_id`

如果 Dify 失败：

- 显式 `rollback`
- 返回 `502`
- 不出现假通过状态

### 3. reject 语义

管理员 reject 时：

- 校验当前条目仍为 `pending`
- `KbSuggestion.status -> rejected`
- 回填：
  - `reviewed_by`
  - `reviewed_at`
  - `reject_reason`

并且：

- **不会创建 `KbEntry`**
- 默认驳回原因为：`管理员驳回`

### 4. 前端最小审核 UI

在统一 `teacher-app` 知识页中：

- 管理员可见 `待审核` tab
- 卡片展示：
  - 标题
  - `representative_query`
  - `scope=global` 标签
  - 提交人 ID
- 操作：
  - `通过`
  - `驳回`
- 驳回支持当前页填写简短原因

审核成功后：

- toast 提示
- 从待审核列表移除
- 同步刷新知识列表

## 与运行现状的偏差

### 偏差 1：审核接口已实现，但 `knowledge_router` 仍未在 `app/main.py` 挂载

当前 `main.py` 仍保留注释挂载：

- `# app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])`

因此当前状态是：

- 代码能力完整
- 测试通过
- 真实运行入口待集成

### 偏差 2：教师侧“驳回后看到最新状态”依赖我的知识列表来源

当前教师端已支持通过本地缓存回显被驳回条目状态；若要完整依赖后端真实列表，仍需后续补齐 `entries` 列表/详情的正式后端实现或已有路由接入。

## 本地校验输出

### pytest

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_knowledge_admin_review.py -q
........                                                                                                      [100%]
8 passed in 0.71s
```

### 审核 + 草稿 + 待补问题回归

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> python -m pytest .\tests\test_knowledge_admin_review.py .\tests\test_knowledge_draft_publish.py .\tests\test_knowledge_unanswered_top.py -q
...................                                                                                           [100%]
19 passed in 0.75s
```

### ruff

```text
All checks passed!
```

## L0-L3 自检结论

### L0

- 已完成
- 管理员可看 global 待审核条目
- 可 approve / reject
- approve 后才真正发 Dify 并写 `kb_entries`

### L1

- 已完成
- 覆盖：
  - 仅管理员可审
  - 待审核列表成功
  - approve 成功
  - reject 成功
  - 重复审核拒绝

### L2

- 待知识路由挂载后做 165 远端联调
- 前端页面已准备好待审核 UI

### L3

- 已确认不影响 `class / college` 直发路径
- `R08-4` 直发测试回归通过

## 驳回原因在教师侧的回显方式

教师端：

- `knowledge/index.vue` 卡片内联展示 `reject_reason`
- `knowledge/detail.vue` 详情页顶部横幅展示 `reject_reason`

## 重复审核保护说明

服务层统一校验：

- 仅 `scope = global && status = pending` 可审核

否则返回：

- `400`
- `该知识条目不可重复审核`

## 165 远端验证建议步骤

在 `knowledge_router` 挂载后执行：

```bash
curl -s "http://192.168.100.165:8100/api/v1/knowledge/reviews/pending?limit=20" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

Approve：

```bash
curl -s -X POST "http://192.168.100.165:8100/api/v1/knowledge/reviews/36/approve" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

Reject：

```bash
curl -s -X POST "http://192.168.100.165:8100/api/v1/knowledge/reviews/37/reject" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reject_reason":"需补充全校适用依据"}'
```

期望：

- approve 返回 `publish_mode = published`
- reject 返回 `entry.status = rejected`
- 重复 approve / reject 返回 `400`
