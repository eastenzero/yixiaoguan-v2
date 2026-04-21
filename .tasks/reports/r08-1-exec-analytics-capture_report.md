# R08-1 Executor Report · chat_analytics 数据采集

## 改动文件

- `services/gateway/alembic/versions/7c7a6f2c4d11_add_chat_analytics.py`
- `services/gateway/app/models/chat_analytics.py`
- `services/gateway/app/models/__init__.py`
- `services/gateway/app/services/analytics.py`
- `services/gateway/app/routers/chat.py`
- `services/gateway/tests/test_analytics_capture.py`
- `services/gateway/requirements.txt`
- `.tasks/reports/r08-1-exec-analytics-capture_report.md`

## 核心实现

### 1. 新增 `chat_analytics` 表与 ORM

已新增：

- `conversation_id`
- `user_id`
- `user_college_id`
- `user_class_id`
- `user_query`
- `query_norm`
- `rag_score`
- `kb_doc_matched`
- `is_answered`
- `created_at`

并补了 3 个索引：

- `idx_chat_analytics_unanswered`
- `idx_chat_analytics_college`
- `idx_chat_analytics_class`

### 2. 在 AI 路径接入 fire-and-forget analytics

接入点位于 `app/routers/chat.py::_stream_ai_response`：

- 仅在 `/api/chat/send` 的 **AI SSE 路径**采集
- 在 `message_end` 里暂存 metadata
- 在最终 `message_end` + `done` SSE **发完之后** 调 `_schedule_chat_analytics(...)`
- 用 `asyncio.create_task(...)` + `async_session()` **新开 session**
- analytics 失败只记 warning，不影响学生主链

### 3. `analytics.py` 设计

#### `normalize_query`

当前算法：

- `strip()` + `lower()`
- 同义替换：
  - `缴纳 -> 交`
  - `缴费 -> 交费`
  - `缴 -> 交`
- 去标点 / 空白
- `jieba.cut`
- 去停用词
- 去重
- 取排序后前 3 个 token，按 `|` 拼接
- 超过 255 截断

停用词包含：

- `的 / 了 / 吗 / 呢 / 呀 / 啊`
- `请问 / 一下 / 一下子 / 一下哈`
- `我 / 想 / 要 / 这个 / 那个`
- `怎么 / 如何`

#### `extract_rag_metrics`

兼容：

- `metadata.retriever_resources`
- `metadata.retrieval_result.records`
- `metadata.retrieval_result` 为 list

取：

- 最高 `score`
- 对应文档名 `document_name | document_title | name`

#### `judge_is_answered`

本轮实际采用：

- **`rag_score is None` -> 直接判 `False`**
- 否则：
  - `rag_score >= 0.3` -> `True`
  - 否则 `response_text` 长度 >= 20 -> `True`

这样可以严格满足任务卡 L0：**未命中时 `is_answered=false`、`rag_score=null`**。

### 4. 为 R08-2 预埋沉淀钩子

虽然 R08-1 scope 不改 `knowledge.py` 结构，但已在 `record_chat_analytics()` 里 **复用现有 `UnansweredQuestion` 模型做聚合沉淀**：

- 当 `is_answered = false` 时
- 按 `question_hash` upsert
- 维护：
  - `question_text`
  - `question_hash`
  - `hit_count`
  - `sample_conv_ids`
  - `college_id`
  - `is_resolved=false`

这样 `R08-2` 可以直接消费已沉淀的 `UnansweredQuestion`，而不是在 GET 时实时扫 `chat_analytics`。

## 与父文档的偏差

### 偏差 1：`user_class_id` 类型修正

父文档 R08 §3.2 写的是 `VARCHAR(64)`；本任务按任务卡要求改为：

- `user_class_id INTEGER`

理由：现有 `User.class_id` 就是整数外键，保持一致更安全。

### 偏差 2：`is_answered` 判定从“长度兜底”收紧为“无命中直接 false”

任务卡 L0 明确要求：

- 未命中时 `is_answered=false`
- `rag_score=null`

因此本轮实现选择：

- **只要 `rag_score is None`，即判 `False`**

这比父文档里的“双条件兜底”更严格，但与任务卡 done criteria 一致，因此按任务卡落地，并在此记录。

## 本地校验输出

### pytest

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_analytics_capture.py -q
..........                                                                                                                                                                                    [100%]
10 passed in 0.74s
```

### R07 回归

```text
PS C:\Users\Administrator\Documents\code\yixiaoguan-v2\services\gateway> pytest tests/test_chat_inputs.py tests/test_ai_pause_resume.py tests/test_teacher_send.py tests/test_escalate_notify.py -q
..........................                                                    [100%]
26 passed, 2 warnings in 1.30s
```

### ruff

```text
All checks passed!
```

### mypy

```text
Success: no issues found in 5 source files
```

## L0-L3 自检结论

### L0

- 已完成
- Dify `message_end` 元数据会被异步采集
- 命中时写 `rag_score / kb_doc_matched`
- 未命中时 `rag_score=None`、`is_answered=False`
- analytics 调度在 `message_end + done` 之后触发，不阻塞学生 SSE 主流

### L1

- 已完成
- `pytest tests/test_analytics_capture.py` 通过
- `R07` 回归测试通过
- `ruff`（scope 文件）通过
- `mypy`（scope 文件）通过

### L2

- 本地未做远端验证
- 待后续 R08 全量任务完成后统一到 `165` 做联调与 SQL 校验

### L3

- 本地未做并发 10 压测
- 待后续 R08 全量任务完成后统一做远端验证

## 为 R08-2 预埋的钩

建议后续 `R08-2` 直接基于 `UnansweredQuestion` 返回榜单，不扫描 `chat_analytics`：

- 排序建议：`hit_count DESC, updated_at DESC, id DESC`
- 待补列表建议过滤：`is_resolved = false`
- 当前 question 聚合键：`question_hash = sha256(query_norm or raw_query.lower())`

## 165 远端验证建议步骤

待统一远端联调时执行：

1. `alembic upgrade head`
2. 学生 token 连续调用 `/api/chat/send` 5 次
3. 执行：

```sql
SELECT id, conversation_id, user_id, user_college_id, user_class_id, user_query, query_norm, rag_score, kb_doc_matched, is_answered, created_at
FROM chat_analytics
ORDER BY id DESC
LIMIT 5;
```

4. 核对：

- 记录数与提问数一致
- 已命中问题具备 `rag_score / kb_doc_matched`
- 未命中问题为 `rag_score=NULL / is_answered=false`

## 新发现的错误模式

- **现象**：父文档中的建议算法可能和任务卡 L0 的硬约束冲突，例如 `is_answered` 既想做“文本长度兜底”，又要求“未命中时必须 false”。
- **正确做法**：当父文档与任务卡的 done criteria 冲突时，应以任务卡为准，并在执行报告里明确记录偏差与原因。
