# R08-4 Executor Report · 润色 / 草稿 / 发布链路

## 改动文件

- `services/gateway/app/models/knowledge.py`
- `services/gateway/alembic/versions/c4a81b9d1e21_r08_scope_publish.py`
- `services/gateway/app/schemas/knowledge.py`
- `services/gateway/app/services/dify_client.py`
- `services/gateway/app/services/knowledge_service.py`
- `services/gateway/app/routers/knowledge.py`
- `services/gateway/tests/test_knowledge_draft_publish.py`
- `.tasks/reports/r08-4-exec-polish-draft-publish_report.md`

## 核心实现

### 1. 复用 `KbSuggestion` 承载草稿与审核态

未新增第二套草稿表，直接扩展 `kb_suggestions`：

- `scope`
- `scope_value`
- `representative_query`
- `question_hash`
- `reject_reason`
- `published_at`

并新增枚举：

- `class`
- `college`
- `global`

对应 migration：

- `c4a81b9d1e21_r08_scope_publish.py`

### 2. 新增提交接口

已实现：

- `POST /api/v1/knowledge/drafts`

请求体：

- `unanswered_question_id`
- `raw_answer`
- `scope`
- `scope_value`

返回体：

- `entry`
- `publish_mode`
  - `published`
  - `pending_review`

### 3. AI 润色 + 降级模板

服务层先尝试：

- `dify_client.polish_text(...)`

若 Dify 润色失败或未配置 key，则降级为本地模板：

- `适用范围：...`
- `问题：...`
- `答复：...`

这样可保证提交链路不断。

### 4. 发布规则

- **`class`**
  - 教师直发
  - 发布 Dify
  - 写入 `kb_entries`
  - `KbSuggestion.status = approved`
- **`college`**
  - 教师直发
  - 发布 Dify
  - 写入 `kb_entries`
  - `KbSuggestion.status = approved`
- **`global`**
  - 不直发
  - 沉淀为 `pending`
  - 交由 R08-5 管理员审核

### 5. 一致性与事务语义

直发链路中：

- 先创建 `KbSuggestion`
- 再调用 Dify 发布
- 成功后写 `KbEntry`
- 同时把 `UnansweredQuestion.is_resolved = true`

若 Dify 失败：

- 显式 `rollback`
- 返回 `502`
- 不留下“前端成功 / 后端未发布”的假状态

## 与父文档 / 运行现状的偏差

### 偏差 1：`class` scope 目前只能用 `current_user.class_id` 做权限来源

仓库中未发现单独的“教师-班级映射”表或服务。当前实现采用最保守权限：

- 教师仅可发布到 `current_user.class_id`

因此：

- 若教师账号无 `class_id`，则不能走 `class` 直发
- 若未来出现一名教师管理多个班级，需要补正式映射来源

### 偏差 2：Dify 润色 key 未单独配置时复用主 `dify_api_key`

`dify_client.polish_text()` 优先读 `dify_polish_api_key`，若不存在则回退 `dify_api_key`。这满足最小闭环，但后续如需隔离权限，建议补独立配置项并纳入 `.env.example`。

### 偏差 3：知识路由仍未在 `app/main.py` 挂载

当前 `services/gateway/app/main.py` 中仍是：

- `# app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])`

为遵守既有任务 scope，本轮未改入口文件，因此当前属于：

- **能力已实现并测试通过**
- **运行入口待后续集成**

## 本地校验输出

### pytest

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_knowledge_draft_publish.py -q
......                                                                                                        [100%]
6 passed in 0.55s
```

### 回归 pytest

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
- 已支持教师提交答复、AI 润色、生成知识条目
- `class / college` 直发
- `global` 进入待审核

### L1

- 已完成
- 测试覆盖：
  - `class` 直发
  - `college` 直发
  - `global` 待审
  - scope 越权
  - Dify 失败回滚
  - 润色失败降级

### L2

- 本地未做 165 远端联调
- 待知识路由入口挂载后验证真实 Dify 发布

### L3

- 已保证不影响 `R08-2` 待补问题列表语义
- 真实 UI 闭环已在 `R08-3` 对接

## 165 远端验证建议步骤

在入口挂载后执行：

```bash
curl -s -X POST "http://192.168.100.165:8100/api/v1/knowledge/drafts" \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "unanswered_question_id": 12,
    "raw_answer": "毕业证补办请联系教务处并提交身份证明材料。",
    "scope": "college",
    "scope_value": 1
  }'
```

期望：

- 返回 `publish_mode = published` 或 `pending_review`
- 直发时返回 `dify_document_id`
- Dify 发布失败时返回非 2xx，且数据库不留下假成功状态
