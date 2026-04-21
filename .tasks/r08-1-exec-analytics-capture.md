---
id: "r08-1-exec-analytics-capture"
parent: "R08-1"
type: "feature"
status: "pending"
tier: "T3"
priority: "medium"
risk: "low"
foundation: true

scope:
  - "services/gateway/alembic/versions/xxxx_add_chat_analytics.py"  # 新建 migration
  - "services/gateway/app/models/chat_analytics.py"                 # 新建 ORM 模型
  - "services/gateway/app/models/__init__.py"                       # 导出新模型
  - "services/gateway/app/services/analytics.py"                    # 新建分析服务
  - "services/gateway/app/routers/chat.py"                          # 仅在 message_end 处加落库调用
  - "services/gateway/tests/test_analytics_capture.py"              # 新建测试
  - "services/gateway/requirements.txt"                             # 如需新增 jieba
  - ".tasks/reports/r08-1-exec-analytics-capture_report.md"

out_of_scope:
  - "services/gateway/app/routers/conversations.py"    # 学生通过 /messages 发的消息不纳入本轮（仅 /chat/send 命中 AI 路径的才统计）
  - "services/gateway/app/routers/actions.py"          # 不动状态机
  - "services/gateway/app/services/state_machine.py"
  - "apps/**"                                          # 不动前端
  - "Dify Chatflow / dify_client 实现"                 # 只消费 message_end 已有事件，不改 Dify 调用
  - "聚类算法 / Top N API / 教师看板 UI"               # 均属于 R08-2 / R08-3 范围
  - "AI 润色 / kb_drafts 表 / KB 发布"                 # 属于 R08-4 / R08-5 范围

context_files:
  - ".teb/antipatterns.md"
  - "docs/requirements/R08-教师-KB-运营闭环.md"                     # 父文档 § 三
  - "docs/requirements/R05-KB-增强需求.md"                          # 历史参考（R05-2 原规划）
  - "services/gateway/app/routers/chat.py"                          # line 129-138 已有 metadata 解析点
  - "services/gateway/app/models/user.py"                           # user.college_id / user.class_id 类型参考
  - "services/gateway/app/models/conversation.py"
  - "services/gateway/alembic/versions/ff1f0ab0c5f8_add_kb_entries_table.py"  # 最近一份 migration 模板

done_criteria:
  L0: "Dify 返回 message_end 事件时，Gateway 落库一条 chat_analytics 记录；命中时 rag_score 取最高匹配分、kb_doc_matched 取 top 命中文档名；未命中时 is_answered=false, rag_score=null；落库过程绝不阻塞 SSE 主流"
  L1: "pytest services/gateway/tests/test_analytics_capture.py 通过；覆盖命中 / 未命中 / metadata 完全缺失三条路径；ruff / mypy 通过；无回归（R07 全部测试保持 PASS）"
  L2: "165 远端 alembic upgrade head 成功；学生 token 调 /api/chat/send 问 5 条问题（含已覆盖与未覆盖），PG 中 SELECT * FROM chat_analytics ORDER BY id DESC LIMIT 5 能看到 5 条完整记录；字段齐全（query_norm / rag_score / kb_doc_matched / is_answered / user_college_id 等）"
  L3: "在 165 远端压一次并发 10 的 /chat/send 请求，全部正常返回 SSE，chat_analytics 落库记录数与请求数一致，服务日志无 analytics 相关异常堆栈"

depends_on: []
created_at: "2026-04-21"
---

# R08-1 Executor · chat_analytics 数据采集

> **目标状态**：每次学生经 `/api/chat/send` 问 AI 之后，Gateway 在 Dify `message_end` 处异步落一条 `chat_analytics` 记录，为 R08-2 聚类统计和 R08-3 教师工作台提供原始数据基础。**本任务是 R08 的最小风险底座**，即使 R08-2/3/4/5 全部延后也不影响现有学生问答链路。

## 背景

`services/gateway/app/routers/chat.py` 第 129-138 行已经在 `_stream_ai_response` 内部消费 Dify 的 `message_end` 事件并提取 `retriever_resources`，用于组装 `sources` 返回给学生端。本任务把这一段事件的**分析维度副产物**（是否命中 / 最高分 / 命中文档名 / 归一化后的 query）落到新表 `chat_analytics`，为 KB 运营闭环提供数据驱动依据。

**不要**把落库当作主流程的一环。分析数据的丢失不应影响学生看到 AI 回复——这是本任务最重要的不变式。

## 必读上下文

1. `docs/requirements/R08-教师-KB-运营闭环.md` § 三（父文档对 R08-1 的目标与数据模型定义）
2. `services/gateway/app/routers/chat.py` 全文（特别是 line 104-181 `_stream_ai_response`）
3. `services/gateway/app/models/user.py` § User / College / Class（确认 `class_id` 是 int 而非 VARCHAR）
4. `services/gateway/alembic/versions/ff1f0ab0c5f8_add_kb_entries_table.py`（最近一份可复用的 migration 写法）
5. `.teb/antipatterns.md`（通用反模式）

## 执行重点

### 1. 数据模型（**对父文档作 1 处类型修正**）

父文档 R08 § 3.2 把 `user_class_id` 写成了 `VARCHAR(64)`。实际 `User.class_id` 是 `int` 外键（见 `@services/gateway/app/models/user.py:53`），本任务按 **INTEGER** 落实，和 User 保持一致；不要做冗余字符串存储。

最终表结构（**以本任务为准**）：

```sql
chat_analytics (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  user_id INTEGER NOT NULL REFERENCES users(id),

  -- 学生维度切片（冗余一份，避免 R08-2 聚合 Top N 时关联 users 表）
  user_college_id INTEGER,                -- 可空：学生身份缺学院时允许 null
  user_class_id INTEGER,                  -- 可空

  -- 查询内容
  user_query TEXT NOT NULL,
  query_norm VARCHAR(255),                -- 归一化后的 fingerprint，用于 R08-2 聚类；可空（归一化失败时保留 null）

  -- RAG 检索结果
  rag_score FLOAT,                        -- null = 未命中
  kb_doc_matched VARCHAR(512),            -- top-1 命中文档名，null = 未命中
  is_answered BOOLEAN NOT NULL,           -- 综合判定

  -- 审计
  created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_chat_analytics_unanswered ON chat_analytics(is_answered, created_at DESC) WHERE is_answered = FALSE;
CREATE INDEX idx_chat_analytics_college ON chat_analytics(user_college_id, created_at DESC);
CREATE INDEX idx_chat_analytics_class ON chat_analytics(user_class_id, created_at DESC);
```

Alembic migration 通过 `alembic revision --autogenerate -m "add chat_analytics"` 生成雏形，人工修正 3 条 partial index 的语义即可。

### 2. `services/gateway/app/services/analytics.py` 设计

纯函数 + 单一 IO 函数组合，便于单测：

```python
# 纯函数
def normalize_query(raw: str) -> str | None:
    """去标点 + 小写 + jieba 分词 + 去停用词 + 取 top-3 关键词拼接，失败返回 None。"""

def extract_rag_metrics(metadata: dict) -> tuple[float | None, str | None]:
    """从 Dify message_end 的 metadata 里提最高 score 和对应文档名。
    兼容 metadata.retriever_resources 和 metadata.retrieval_result 两种字段名。"""

def judge_is_answered(
    rag_score: float | None,
    response_text: str,
    *,
    score_threshold: float = 0.3,
    min_answer_length: int = 20,
) -> bool:
    """双条件兜底：有 rag_score>=阈值 或 文本长度>=阈值 即视为已回答。"""

# IO 函数（唯一一处与 DB 交互）
async def record_chat_analytics(
    db: AsyncSession,
    *,
    conv_id: int,
    user: User,
    raw_query: str,
    response_text: str,
    dify_metadata: dict,
) -> None:
    """组装字段 + INSERT。绝不抛异常给上层；所有 Exception 吃掉并 logger.warning。"""
```

### 3. 在 `chat.py` 接入的唯一一处

在 `_stream_ai_response` 的 `message_end` 分支（当前 line 129-138）之后，或在整个生成器**收尾保存 AI 消息时**（line 151-166 之后），**以 fire-and-forget 方式**调 `record_chat_analytics`。

推荐位置（不必放在 yield message_end 之前，避免前端拿到回复前做任何多余 IO）：

```python
# line 166 之后、line 168 之前，已经 commit 完毕
asyncio.create_task(
    record_chat_analytics(
        db_session_factory(),           # 不能直接复用 db（会话已被主流 commit 过），新开一个 session
        conv_id=conv.id,
        user=user,
        raw_query=query,
        response_text=full_answer,
        dify_metadata=last_message_end_metadata,   # 需要在 message_end 分支里暂存
    )
)
```

**关键点**：

- **必须新开 session**：`_stream_ai_response` 的 `db` 参数在主流结束后可能已被关闭/commit；analytics 落库要独立一个 AsyncSession，避免干扰主流事务
- **fire-and-forget**：用 `asyncio.create_task` 而不是 `await`，确保学生已经拿到 `message_end` + `done` SSE 后再异步落库
- **绝对吃掉异常**：`record_chat_analytics` 内部 try/except 整段，任何错误只 `logger.warning`

### 4. 测试策略

`tests/test_analytics_capture.py` 至少覆盖以下 case（沿用 `conftest.py` 已有的 fixture 风格）：

1. **命中路径**：mock Dify 返回带 retriever_resources（分数 0.85 + 文档名 "电费缴纳.md"），断言落库记录 `rag_score=0.85` / `kb_doc_matched="电费缴纳.md"` / `is_answered=True`
2. **未命中路径**：mock Dify 返回 `retriever_resources=[]`，断言 `rag_score is None` / `kb_doc_matched is None`
3. **metadata 字段缺失**：mock Dify 返回 `message_end` 时没有 `metadata` 键（Dify 异常版本可能），断言不抛异常、落一条 `rag_score=None` 的记录
4. **`normalize_query` 纯函数**：单独测"怎么交电费" / "电费怎么缴" / "  电费缴纳？  " 三种输入产出同一 fingerprint
5. **`extract_rag_metrics` 兼容性**：分别喂 `retriever_resources` 和 `retrieval_result` 两种字段名，都能正确提取
6. **异常不冒泡**：mock `db.add` 抛 IntegrityError，断言 `_stream_ai_response` 仍正常返回完整 SSE（不能因为 analytics 失败而 hang 学生端）

## 已知陷阱

- **阻塞主流是红线**：不要把 `await record_chat_analytics(...)` 放在 `yield event: done` 之前。学生端拿到 `done` 前看到的任何延迟都是本任务造成的用户体验损耗
- **session 复用陷阱**：`_stream_ai_response(db, ...)` 的 `db` 是主流的 AsyncSession，已经在 line 166 `commit` 过一次。如果直接在它上面 `db.add(ChatAnalytics(...))` 再 `commit`，会和主流提交时机竞争。**必须新开 session**
- **jieba 首次加载慢（首次 ~1s）**：要么在 `analytics.py` 顶部 `import jieba; jieba.initialize()` 预热；要么测试里 mock 掉分词。不要让首个学生请求吃这个延迟
- **query_norm 过长截断**：VARCHAR(255) 上限，如果归一化后 fingerprint 偶然超长（不常见但理论可能），要截断不要抛异常
- **Dify metadata 版本差异**：目前项目用的 Dify 版本里字段名是 `retriever_resources`（见 `@services/gateway/app/routers/chat.py:132`），但 Dify 历史版本有用过 `retrieval_result` 的；`extract_rag_metrics` 要做兼容
- **`is_answered` 阈值是可调的**：默认 0.3 + 20 字，如果真实跑起来发现判错率高（如 AI 礼貌性回复"不知道呢"被判 True），在本任务范围里不要改阈值，只需把阈值做成 config（环境变量或 settings 常量）让 TX 后续能调
- **R08-2 的聚类会依赖 query_norm**：本任务产出的 `query_norm` 格式会被 R08-2 消费，本轮要把归一化算法写清楚并在报告里说明，后续 R08-2 不要再改这个算法；要改必须通过新 migration 或后台 backfill

## 报告应包含

在 `.tasks/reports/r08-1-exec-analytics-capture_report.md` 中：

1. 最终 migration 文件名与 revision hash
2. `normalize_query` 的具体算法（哪些标点、停用词来源、取 top-N 的 N 值）
3. `is_answered` 的判定规则与默认阈值
4. 本轮未处理但为 R08-2 埋的钩（如"聚类建议使用 query_norm 精确相等 + `kb_doc_matched IS NULL OR rag_score < 0.3` 过滤"）
5. 165 远端 alembic upgrade 与 5 条真实问答落库的截图或 SQL 输出

## 回滚方案

- `alembic downgrade -1` 退回 migration
- Git revert 本次改动
- 回滚不影响历史数据（因 chat_analytics 是新表，回滚即删表）
- 回滚不影响学生主流问答（chat.py 里的调用是 fire-and-forget，移除后学生体验无感知）
