# R08 — 教师 KB 运营闭环（P1）

> **创建日期**：2026-04-21
> **作者**：T0（TX 授权起草）
> **状态**：📝 **规划中**。父文档起草完成，待 TX 审阅后拆 `.tasks/` 进入 T3 实施轨道
> **定位**：把"学生问题统计 → 教师答复 → AI 润色 → KB 入库"做成**主动运营闭环**，让 KB 从"静态初装"进化为"基于真实使用数据持续增长"
> **前置阅读**：
> - `docs/requirements/R05-KB-增强需求.md` 需求 2（高频无答案问题统计，提供数据基础）
> - `docs/requirements/R01-既有开发意向汇总.md` § 闭环 A（问答与知识增长，给出整体框架）
> - `docs/requirements/R02-师生对话与主动运营.md` 需求 4（定制导员，本 R08 是其数据驱动基础）
> - `docs/requirements/R03-开发前确认事项.md` § C3（知识审核角色约定，**本 R08 对其作细化调整，已与 TX 对齐**）
> - `docs/requirements/R07-师生对话核心闭环.md`（R08 的教师工作台建立在 R07 的师生对话能力之上）

---

## 总览

| ID | 任务 | 类型 | 预计工时 | 风险 | 依赖 |
|----|------|------|---------|------|------|
| **R08-1** | 数据采集：`chat_analytics` 表 + Gateway 解析 Dify `message_end` metadata | 代码 + 测试 | 2-3 h | 低 | R05-2 数据模型 |
| **R08-2** | 聚类统计：未命中/低置信度 query 的归一聚类 + Top N 榜单 API | 代码 + 测试 | 3-4 h | 中（算法选型） | R08-1 |
| **R08-3** | 教师工作台：「高频待补知识」页面 + "我来回答"入口 | 前端 + 代码 | 3-4 h | 中（UI 交互） | R08-2 + R07 教师端基线 |
| **R08-4** | AI 润色 + 草稿落库：教师答复 → LLM 润色 → `kb_drafts` 表 | 代码 + 测试 | 3-4 h | 中（prompt 契约） | R08-3 + Dify 链路 |
| **R08-5** | KB 发布：**学院/班级直发**；**全校走管理员审核** | 代码 + 测试 | 2-3 h | 高（权限 + Dify KB API） | R08-4 |

**合计**：13-18 h T3 实施 + 2-3 h T0 审阅 + 1-2 h TX 远端冒烟

---

## 一、背景与目标

### 1.1 为什么要做

1. **R05-2 只做了一半**：原规划只到"Top 未覆盖问题看板"给**管理员**看，没规划"**谁回答 → 怎么变成 KB**"这条生产路径
2. **R01 闭环 A 有框架但没细节**：写了"教师人工处理 → 转知识草稿"，但没定义 AI 润色、权限边界、发布对接
3. **KB 初装后会衰减**：当前 KB 是从学生手册等静态材料冷启动（~835 条），学生真实问题里一定有盲区，必须有**自生长机制**
4. **R07 已经铺好底座**：师生对话闭环完成后，教师端已经能看到学生提问、能介入会话，**顺势把"教师答复 → KB 增量"这条运营链路接上，边际成本最低**

### 1.2 最终目标

当 R08 完成后：

- Gateway 每次 AI 回答后自动记录命中/未命中分析数据
- 教师工作台出现新 Tab「高频待补知识」，展示**本学院/本班**未覆盖 Top N 问题
- 教师点"我来回答" → 填写答复（可口语化）→ 系统调 AI 润色为 KB 规范文风
- 学院/班级范围的条目：**教师即点即发**，同步写入 Dify KB（或自建 KB）对应 dataset
- 全校范围的条目：进入 `kb_drafts` 待管理员审核后发布
- 下一次同类问题出现时，AI 能直接命中新入库的条目

---

## 二、权限模型（**TX 定稿**）

> "如果老师回答的问题是属于他学院或者是班级范围的，就直接发布。如果是涉及到全校的，就经由审核。"
> ——TX，2026-04-21

### 2.1 作用域 `scope` 字段

教师在答复时**必填**的字段，三选一：

| scope | 含义 | 教师可选性 | 审核流程 |
|-------|------|-----------|---------|
| `class` | 仅作用于某个班级 | 教师只能选自己**任教**的班级 | ✅ 教师直发 |
| `college` | 仅作用于某个学院 | 教师只能选自己**所属**学院（默认值） | ✅ 教师直发 |
| `global` | 全校通用 | 任何教师都可选 | ⛔ 进入管理员审核队列 |

### 2.2 默认立场

- **默认 scope = `college`**：教师通常在自己学院范围答题，UI 默认选中本学院，**鼓励轻流程**
- **`class` 需要任教映射**：需要 `teacher_classes` 关联表（R08-3 建表）确定教师能管哪些班
- **`global` 审核节奏**：管理员审核页面按到达时间排序；审核通过即发布，不支持二次编辑（保证教师答复的原意，如需修改打回让教师改）
- **越权兜底**：后端 scope 校验必须严于前端，前端不显示不代表后端不校验

### 2.3 与 R03 原约定的关系

R03 § C3 原文：**"知识审核等均由管理员负责"**。

本 R08 把这条细化为：

- **全校 KB 由管理员审核**（保留 R03 原意）
- **学院/班级 KB 由教师直发**（新增，降低运营摩擦）

> R03 原文层面不需要改（它说的是"审核"这件事归属管理员；教师直发的是**不需要审核**的部分，逻辑自洽）。但 R03 后续版本可补一条备注引用 R08。

---

## 三、R08-1 · 数据采集

### 3.1 目标状态

每次 AI 回答结束，Gateway 自动落库一条 `chat_analytics`，包含用户原始 query、RAG 命中情况、置信度、AI 是否给出了有效答复。

### 3.2 数据模型

沿用 R05-2 的设计，**补充 4 个字段**以支持后续聚类与维度切片：

```sql
chat_analytics (
  id SERIAL PRIMARY KEY,
  conversation_id VARCHAR(128) NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id),

  -- 学生维度切片（用于 R08-2 按学院/班级聚合）
  user_college_id INTEGER,       -- 新增：学生所在学院 ID（冗余一份，避免查询时关联）
  user_class_id VARCHAR(64),     -- 新增：学生所在班级 ID

  -- 查询内容
  user_query TEXT NOT NULL,
  query_norm TEXT,               -- 新增：归一化后的 query（去标点、小写、分词），用于 R08-2 聚类

  -- RAG 检索结果
  rag_score FLOAT,               -- 最高匹配分数，null = 未命中
  kb_doc_matched VARCHAR(255),   -- 命中的 KB 文档标识
  is_answered BOOLEAN NOT NULL,  -- AI 是否给出了有效回答（由 Gateway 根据 metadata + 文本长度判断）

  -- 审计
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chat_analytics_unanswered ON chat_analytics(is_answered, created_at DESC) WHERE is_answered = FALSE;
CREATE INDEX idx_chat_analytics_college ON chat_analytics(user_college_id, created_at DESC);
CREATE INDEX idx_chat_analytics_class ON chat_analytics(user_class_id, created_at DESC);
```

### 3.3 改动范围（预估）

| 组件 | 改动 |
|------|------|
| `services/gateway/alembic/versions/xxxx_add_chat_analytics.py` | 建表 + 3 个索引 |
| `services/gateway/app/models/chat_analytics.py` | SQLAlchemy 模型 |
| `services/gateway/app/routers/chat.py` | Dify `message_end` 事件解析 + 落库 |
| `services/gateway/app/services/analytics.py` | `query_norm` 归一化、`is_answered` 判定逻辑 |
| `services/gateway/tests/test_analytics_capture.py` | 命中/未命中/异常三种路径 |

### 3.4 验收标准

| 层级 | 判定 |
|------|------|
| L0 | Dify 返回 `message_end` 时 Gateway 落库一条 `chat_analytics`；命中时 `rag_score` 与 `kb_doc_matched` 正确；未命中时 `is_answered=false` |
| L1 | pytest 覆盖命中/未命中/metadata 缺失兜底；ruff / mypy 通过 |
| L2 | 165 远端通过学生 token 问 10 条问题，PG 表能看到 10 条记录，字段完整 |
| L3 | 未覆盖（属于 R08-2 的验收面） |

---

## 四、R08-2 · 聚类统计

### 4.1 目标状态

把 `chat_analytics` 里 `is_answered=false` 或 `rag_score < threshold` 的 query 聚类合并（"电费怎么交" / "交电费" / "电费缴纳" 归为一类），按频次输出 Top N 榜单 API，支持按学院/班级过滤。

### 4.2 聚类算法（默认立场）

**简化版（P1 默认）**：

1. `query_norm` 已在 R08-1 做了基本归一（去标点、小写、jieba 分词）
2. 取 jieba 关键词 Top 3 作为 fingerprint
3. 相同 fingerprint 归为同一簇
4. 每簇取第一个 query 作为"代表问题"展示，附带簇内样本数

**进阶版（P2 可选，本轮不做）**：

- 调 Dify 或 sentence-transformer 做 embedding
- 用 DBSCAN/k-means 做向量聚类
- 对同义但关键词不同的 query（如"怎么请假" vs "病假怎么办"）更友好

### 4.3 API 契约

```
GET /api/analytics/unanswered_top
  ?scope=college|class|all
  &scope_value=<college_id|class_id>
  &window_days=7
  &limit=20

Response:
{
  "total": 123,
  "window_start": "2026-04-14T00:00:00Z",
  "items": [
    {
      "cluster_id": "a3f2...",
      "representative_query": "怎么交电费",
      "sample_queries": ["怎么交电费", "电费怎么缴", "交电费操作"],
      "count": 27,
      "latest_at": "2026-04-21T09:12:00Z",
      "student_colleges": ["临床与基础医学院", "公共卫生学院"]
    }
  ]
}
```

### 4.4 验收标准

| 层级 | 判定 |
|------|------|
| L0 | 教师调 `/analytics/unanswered_top?scope=college&scope_value=<本学院>` 返回本学院未覆盖 Top N，含簇内样本与次数 |
| L1 | pytest 覆盖：同关键词归一、不同关键词分开、跨学院不串、权限越权 403；ruff / mypy 通过 |
| L2 | 165 远端通过预先埋入 20 条假数据 + 教师 token 调 API，返回聚类结果人工目视合理 |
| L3 | 教师能基于榜单 `cluster_id` 发起 R08-3 的"我来回答"流程 |

---

## 五、R08-3 · 教师工作台页面

### 5.1 目标状态

教师端（`apps/teacher-app`）新增一个 Tab「高频待补知识」，展示 R08-2 的榜单，每条支持：

- 展开查看该簇内学生的原始问题样本（至多 10 条）
- 查看该簇的时间分布（最近一次 / 历史累计）
- 点击"我来回答" → 进入 R08-4 的答复编辑页

### 5.2 页面交互草案

```
┌──────────────────────────────────────────┐
│ Tab: 工单 │ 会话 │ 【高频待补知识】│ 我的  │
├──────────────────────────────────────────┤
│ 筛选：[本学院 ▾] [近 7 天 ▾]  [刷新]     │
├──────────────────────────────────────────┤
│ #1  怎么交电费     (27 次，最近 2h 前)    │
│     样本：怎么交电费 / 电费怎么缴 / ...     │
│     [展开 3 条] [我来回答 →]              │
├──────────────────────────────────────────┤
│ #2  图书馆座位预约 (18 次，最近 30m 前)   │
│     ...                                  │
└──────────────────────────────────────────┘
```

### 5.3 改动范围（预估）

| 组件 | 改动 |
|------|------|
| `apps/teacher-app/src/pages/kb-feed/*` | 新页面（list + detail） |
| `apps/teacher-app/src/api/analytics.ts` | API wrapper |
| `apps/teacher-app/src/stores/kb-feed.ts` | 列表状态（筛选、分页） |
| `services/gateway/app/models/teacher_classes.py` | **新表**：教师-班级映射（决定 `scope=class` 可选范围） |
| `services/gateway/app/routers/analytics.py` | `/analytics/unanswered_top` + scope 权限校验 |

### 5.4 验收标准

| 层级 | 判定 |
|------|------|
| L0 | 教师打开教师端能看到「高频待补知识」Tab 并拉到列表 |
| L1 | 前端单测 + 后端 pytest 覆盖权限（教师 A 看不到教师 B 学院的数据） |
| L2 | 165 远端 UI 上点进一条能展开样本；"我来回答"跳转 R08-4 页面 |
| L3 | 管理员账号打开时看到"管理员请到审核页"提示，不误用该 Tab |

---

## 六、R08-4 · AI 润色 + 草稿落库

### 6.1 目标状态

教师在"我来回答"页面填写答复（可口语化、可短小），提交后：

1. Gateway 调 LLM 润色成 KB 规范
2. 结果展示给教师预览（可编辑、可放弃润色用原文）
3. 教师确认 `scope` 并提交 → 写入 `kb_drafts` 表

### 6.2 AI 润色链路

**调用方**：Gateway

**被调方**：优先走 **Dify `/v1/chat-messages`**（新建一个"KB 润色助手"Bot），保持统一 AI 调用链；回退方案是直调 DeepSeek API（若后续要自建 LLM 也只改这一处）

**Prompt 契约**（Dify Bot 配置）：

```
System：
你是一个校园知识库编辑助手。用户会给你一段教师针对学生问题的答复草稿，
你的任务是改写为标准 KB 条目，要求：
1. 保留教师答复的所有事实信息（不得增删关键步骤）
2. 结构化：标题 + 适用范围 + 3-5 段正文 + 可选的注意事项
3. 语气：正式、清晰、面向学生
4. 长度：150-400 字
5. 末尾不加署名

输入：教师针对"{{representative_query}}"的答复：{{raw_answer}}

输出格式（JSON）：
{
  "title": "标题",
  "applicable_scope": "适用范围描述",
  "body": "正文（Markdown）",
  "tutorial_tag": null  // 如涉及 App 操作步骤，可填 "[tutorial:xxx]"
}
```

**容错**：润色超时/解析失败 → 回退到"原文 + 最小格式化"（自动加标题 = representative_query），**不阻塞教师发布**。

### 6.3 数据模型

```sql
kb_drafts (
  id SERIAL PRIMARY KEY,
  cluster_id VARCHAR(64),                    -- 从 R08-2 带过来，便于追溯数据来源
  representative_query TEXT NOT NULL,        -- 发起时的代表问题
  raw_answer TEXT NOT NULL,                  -- 教师原始答复

  polished_title VARCHAR(255),
  polished_body TEXT,
  polished_applicable_scope TEXT,
  polish_status VARCHAR(16) NOT NULL,        -- 'polished' | 'fallback' | 'skipped'

  scope VARCHAR(16) NOT NULL,                -- 'class' | 'college' | 'global'
  scope_value VARCHAR(128),                  -- scope=class 时班级 ID；scope=college 时学院 ID

  submitted_by INTEGER NOT NULL REFERENCES users(id),
  submitted_at TIMESTAMP DEFAULT NOW(),

  status VARCHAR(16) NOT NULL,               -- 'pending_publish' | 'pending_review' | 'published' | 'rejected'
  published_at TIMESTAMP,
  published_kb_entry_id VARCHAR(128),        -- 发布到 Dify KB / 自建 KB 后得到的外部 ID

  reviewer_id INTEGER REFERENCES users(id),  -- 管理员（scope=global 时填）
  reviewed_at TIMESTAMP,
  reject_reason TEXT
);

CREATE INDEX idx_kb_drafts_status ON kb_drafts(status, submitted_at);
CREATE INDEX idx_kb_drafts_scope ON kb_drafts(scope, scope_value);
```

### 6.4 验收标准

| 层级 | 判定 |
|------|------|
| L0 | 教师提交答复 → 看到润色预览 → 确认 scope → 成功写入 `kb_drafts` |
| L1 | pytest 覆盖：润色成功 / 润色失败降级 / scope 越权被拒 / scope=global 必填字段 |
| L2 | 165 远端端到端：教师提交一条，PG 表能看到完整记录，polish_status=polished |
| L3 | 预览页面支持编辑润色后内容（教师有最终控制权） |

---

## 七、R08-5 · KB 发布

### 7.1 目标状态

根据 `scope` 执行分支发布：

```
if scope in ('class', 'college'):
    → status = 'pending_publish'
    → 立即调 KB 发布 API（Dify 或自建）
    → 成功 → status = 'published' + published_kb_entry_id
    → 失败 → 告警 + 保留 pending_publish，后台重试
elif scope == 'global':
    → status = 'pending_review'
    → 写入管理员待审核队列
    → 管理员审核页面：通过 → 同上发布；驳回 → status='rejected' + reject_reason
```

### 7.2 KB 发布接口选型

**候选 A：对接 Dify KB Document API**（默认）

- Dify 支持通过 API 向指定 dataset 新增 document
- 按 scope 维护不同 dataset：`kb-global` / `kb-college-{id}` / `kb-class-{id}`
- 好处：保持 Dify 为 RAG 入口，与现有 `migrate_kb.py` 一致
- 风险：Dify dataset 数量上限（免费版通常够，需 TX 确认配额）

**候选 B：自建 KB 表 + pgvector**（作为 RAG/LLM 自建线的一部分）

- 写入 gateway 本地 `kb_entries` 表（已有模型），embedding 入 pgvector
- 好处：为 TX 最初那个"Dify 替代"主线铺路
- 风险：需要 Gateway 侧自己实现检索逻辑，工程量外溢

**默认立场**：**候选 A（对接 Dify KB）**。简单、不扩工程面；如果将来主线转自建 RAG，只要把 `publish_to_kb()` 这个函数的实现替换即可。

### 7.3 管理员审核页面（为 `scope=global`）

- 复用已有管理端骨架（若 R08 前尚无管理端，在此 batch 一起起骨架页）
- 列表按 `submitted_at` 排序；详情页显示：教师原文 / AI 润色文本 / 教师预览编辑后文本 / scope 说明
- 操作：通过 / 驳回（驳回必须填 reason）

### 7.4 验收标准

| 层级 | 判定 |
|------|------|
| L0 | `scope=college` 提交 → 直发成功；`scope=global` → 进审核队列；管理员审核通过后发布成功 |
| L1 | pytest 覆盖发布成功 / Dify API 失败重试 / 审核通过链路 / 审核驳回链路 |
| L2 | 165 远端：教师直发一条学院 KB，然后学生问相关问题能命中该条目 |
| L3 | 管理员驳回后，教师收到 WS 通知 + 在工作台看到"被驳回待修改"提示 |

---

## 八、与其他需求的关系

| 关系方 | 交集 | 处理 |
|--------|-----|------|
| **R05-2 高频统计** | R08-1 + R08-2 覆盖了 R05-2 的数据层和统计层 | R05-2 视为 R08 的子集吸收；完成后 R05-2 状态置 ✅（由 R08 承接） |
| **R01 闭环 A** | R08-3/4/5 落地了"教师处理 → 知识草稿 → 审核发布" | R08 即是 R01 闭环 A 的正式工程化版本 |
| **R02 需求 4 定制导员** | 定制导员是"AI 判断 + 自动介入"升级版；R08 是其数据基础 | R08 完成后才讨论 R02-4 的 AI 判断门槛 |
| **R03 § C3 审核角色** | R03 原文"审核由管理员负责"；R08 补"学院/班级直发"分支 | 本 R08 § 2.2 已明确对齐，不改 R03 |
| **R05-1 Top 10 图文教程** | 润色 prompt 预留 `tutorial_tag` 字段，未来可挂 `[tutorial:xxx]` | R08 不主动生成 tutorial，但不阻塞后续挂接 |
| **R07 师生对话** | R08-3 教师工作台页面建立在 R07 教师端骨架之上 | R07 已完成，R08 可直接接 |
| **Dify 替代主线（RAG/LLM 自建）** | R08-5 的 `publish_to_kb()` 是未来切换点 | 本 R08 默认对接 Dify KB，切换时只改这一个函数 |

---

## 九、执行顺序与依赖

```
┌─ batch-1（数据底座）───────────────────────┐
│  R08-1 数据采集                            │
│  交付后 Gateway 就开始积累真实分析数据     │
└──────────────────────────────────────────┘
                    │
┌─ batch-2（统计 + 教师入口）───────────────┐
│  R08-2 聚类统计       │ 并行可行          │
│  R08-3 教师工作台     │                   │
└──────────────────────────────────────────┘
                    │
┌─ batch-3（生产闭环）──────────────────────┐
│  R08-4 AI 润色 + 草稿                     │
│  R08-5 KB 发布                            │
│  （R08-5 依赖 R08-4，R08-4 依赖 R08-3）   │
└──────────────────────────────────────────┘
                    │
┌─ batch-4（端到端冒烟）────────────────────┐
│  scripts/r08-e2e-smoke.py                 │
│  模拟学生提问 → 教师答复 → 润色 → 发布 →   │
│  下一次学生提问命中新条目                  │
└──────────────────────────────────────────┘
```

**建议节奏**：

- batch-1 独立上线（先让数据流起来，哪怕上层暂无消费者）
- batch-2/3 可等 batch-1 积累 3-7 天真实数据后再做，避免"聚类算法对假数据调得很准、真数据上翻车"
- batch-4 作为收尾回归资产，同 R07 `scripts/r07-e2e-smoke.py` 形式

---

## 十、风险与未决点

### 10.1 已识别风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| **Dify KB API 速率限制** | R08-5 直发失败率上升 | 加重试 + 告警；真扛不住时批量异步合并写 |
| **润色 prompt 偏差** | AI 改写后的文本丢事实 / 加幻觉 | 教师必经预览确认环节；polished 文本与 raw_answer 都留底；支持回退原文 |
| **聚类算法过粗/过细** | Top N 榜单要么全是噪音要么把真同义问题拆开 | 先用简化版上线，积累数据后再决定是否上 embedding 版；阈值可配置 |
| **教师任教班级映射空白** | `scope=class` 几乎无教师可选 | R08-3 新表 `teacher_classes`，初期可由管理员批量导入；前端在映射为空时隐藏 `class` 选项 |
| **全校审核队列堆积** | 管理员疏于处理，教师提交后石沉大海 | 管理员端显示待审核红点；超过 7 天自动 @ 管理员 WS 提醒 |

### 10.2 未决点（需要 TX 或后续迭代明确）

1. **KB 入 Dify 的 dataset 粒度**：`kb-global` / `kb-college-{id}` / `kb-class-{id}` 三级够不够？还是 `kb-college-{id}` 下按班级打标签就行？
2. **润色 LLM 选型**：Dify 里的润色 Bot 用什么模型？建议用比主 Chatflow 更轻的（如 DeepSeek-Chat），降本增效
3. **教师答复 → 学生可见时效**：直发到 Dify KB 后，学生多快能命中？（Dify 文档入库到可检索有 embedding 处理延迟，需要实测）
4. **草稿返工流程**：教师被驳回后怎么修改？在原草稿上编辑还是新建一份？（建议在原草稿上改，保留历史 reject_reason）

---

## 十一、交付物清单（R08 完成时应有）

- [ ] `services/gateway/alembic/versions/xxxx_add_chat_analytics_and_kb_drafts.py`
- [ ] `services/gateway/app/models/{chat_analytics.py, kb_drafts.py, teacher_classes.py}`
- [ ] `services/gateway/app/services/{analytics.py, kb_publisher.py, llm_polisher.py}`
- [ ] `services/gateway/app/routers/{analytics.py, kb_drafts.py, kb_review.py}`
- [ ] `services/gateway/tests/{test_analytics_*.py, test_kb_drafts_*.py, test_kb_publish_*.py}`
- [ ] `apps/teacher-app/src/pages/kb-feed/*`
- [ ] 管理员端审核页（若无管理端骨架，在此 batch 起骨架）
- [ ] `scripts/r08-e2e-smoke.py`
- [ ] `.tasks/r08-*.md` 任务卡 + `.tasks/reports/r08-*-report.md` 执行报告
- [ ] `docs/requirements/R08-教师-KB-运营闭环.md` 逐批次更新状态与变更日志

---

## 十二、变更日志

| 日期 | 变更 | 作者 |
|------|-----|------|
| 2026-04-21 | 首版起草：5 子任务拆分 + 权限模型（TX 定稿：学院/班级直发、全校审核）+ 数据模型 + 发布链路 | T0（TX 授权） |
