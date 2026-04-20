# 去 Dify 化架构迁移方案

> 创建日期：2026-04-16
> 状态：**已确认，待排期执行**
> 来源：与 TX 讨论确认

---

## 一、背景与动机

Dify 自建部署启动占用 4-8GB 内存（含 Redis、PostgreSQL、Worker、API Server、Web 等多个容器），线上部署时资源负担过重。当前 Dify 同时承担三个职责：

1. **意图分类**：qwen-plus, temperature=0.1，四分类（greeting/chitchat/kb_query/transfer）
2. **知识库检索**：multimodal-embedding-v1 + qwen3-rerank，语义搜索 Top 3
3. **LLM 回答生成**：qwen-plus, temperature=0.7，带 context 注入 + 10 条历史记忆窗口

这三个能力均可通过通义千问云端 API 直接实现，无需 Dify 作为中间层。

### 资源对比

| 方案 | 组件 | 内存占用 |
|------|------|---------|
| 当前（Dify） | Gateway + Dify (4-8GB) + PG + Redis | 约 6-10GB |
| 自建 | Gateway + pgvector (PG 已有) + Redis | 约 1-2GB |

---

## 二、目标架构

```
客户端（学生端 UniApp / 教师端 Web）
    ↓
Gateway (Python FastAPI, 端口 8100)
    ├── IntentClassifier      → 通义千问 API (qwen-plus, temperature=0.1)
    ├── KnowledgeRetriever    → PG pgvector
    │     ├── Embedding       → 通义千问 text-embedding-v3
    │     └── Rerank          → 通义千问 qwen3-rerank (可选)
    ├── LLMService            → 通义千问 API (qwen-plus, streaming SSE)
    └── ConversationMemory    → PG messages 表 (已有)
```

### 关键设计原则

- **LLM 服务可插拔**：通过统一接口封装，后续可切换为其他云端 API 或本地模型
- **前端零改动**：SSE 流式协议不变，前端无感知
- **渐进式替换**：每个阶段独立可验证，不一次性切换

---

## 三、分阶段执行计划

### 阶段 0：当前（不动 Dify，先完成 KB 数据清洗）

KB 数据清洗工作与架构无关，可以先推进：
- 三路数据源清洗（W1/W2/W3）产出结构化 MD 文件
- 文件格式遵循 `kb-pipeline/KB-SPEC.md` 的 V2 规范
- 输出到 `kb-pipeline/04-output/merged/` 目录

同时入库 Dify（使用现有 Dataset API + `scripts/migrate_kb.py`），保证系统可用。
**本地 MD 文件保留**，作为将来自建 KB 的原料。

---

### 阶段 1：自建知识库检索（替换 Dify 的 Knowledge Retrieval 节点）

**目标**：Gateway 自己做 RAG 检索，不再依赖 Dify Dataset API。

**核心改动**：

#### 1.1 PG 启用 pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

复用现有 PostgreSQL（yixiaoguan_v2），零额外部署成本。

#### 1.2 新建 `app/services/embedding_service.py`

- 调通义千问 `text-embedding-v3` API 生成文本向量
- 支持单条和批量 embedding
- 入库时预计算向量存入 PG

#### 1.3 新建 `app/services/knowledge_service.py`

- query → embedding → pgvector 向量相似度搜索 → Top K
- 可选：调通义千问 rerank API 对检索结果重排序
- 返回格式与当前 Dify 的 `retriever_resources` 对齐，方便对比

#### 1.4 新建入库脚本 `scripts/import_kb_v2.py`

- 读取 `04-output/merged/*.md`，解析 V2 frontmatter
- 按 `##` 标题切分为独立段落（与 Dify 的 automatic 分段策略对齐）
- 调 embedding API 生成向量
- 写入 PG：`kb_chunks` 表（段落+向量）+ `kb_entries` 元数据表

#### 1.5 数据库 migration

`kb_entries` 表调整：
- **新增**：`doc_id` (VARCHAR, 如 KB-V2-C02-001)、`sources` (JSONB)、`last_verified` (DATE)
- **移除**：`dify_document_id`、`dify_dataset_id`（阶段 2 完成后）
- 阶段 1 期间**暂时保留** Dify 字段，两套并存

新建 `kb_chunks` 表：
```
kb_chunks (
    id SERIAL PRIMARY KEY,
    kb_entry_id INTEGER REFERENCES kb_entries(id),
    chunk_index INTEGER NOT NULL,          -- 段落在文档中的顺序
    heading TEXT,                           -- ## 标题
    content TEXT NOT NULL,                  -- 段落正文
    embedding vector(1024),                -- text-embedding-v3 维度
    created_at TIMESTAMP DEFAULT NOW()
)
```

**此阶段 Dify 仍在运行**，两套并存验证效果。可通过配置开关切换：

```python
# config.py
use_self_rag: bool = False  # True 时使用自建 RAG，False 时走 Dify
```

---

### 阶段 2：自建意图分类 + LLM 回答（完全替换 Dify Chatflow）

**目标**：Gateway 直接调通义千问 API 完成全流程，彻底移除 Dify。

#### 2.1 新建 `app/services/intent_classifier.py`

直接调通义千问 qwen-plus，system prompt 复用 Dify 现有分类指令：

```python
INTENT_SYSTEM_PROMPT = """你是一个意图分类器。根据用户的输入，判断其意图类别。

分类规则：
- greeting: 问候语（你好、嗨、早上好、在吗 等）
- chitchat: 闲聊（谢谢、再见、你是谁、你叫什么 等非校园事务）
- kb_query: 校园事务咨询（任何关于学校规则、流程、时间、地点的问题）
- transfer: 明确要求转人工（找老师、转人工、人工客服 等）"""
```

本质上就是一次 LLM 调用 + JSON 输出解析，逻辑极其简单。

#### 2.2 新建 `app/services/llm_service.py`

封装通义千问 Chat API（流式 SSE），支持：
- system prompt + context 注入
- 历史消息窗口（从 PG messages 表取最近 N 条）
- 流式输出（SSE / OpenAI 兼容格式）
- 可插拔接口（后续可切换供应商）

```python
class LLMService:
    async def chat_stream(
        self,
        messages: list[dict],       # [{"role": "system", "content": "..."}, ...]
        temperature: float = 0.7,
        stream: bool = True,
    ) -> AsyncGenerator[str, None]:
        """流式调用通义千问，yield 每个 token"""
        ...
```

#### 2.3 改造 `app/routers/chat.py` 中的 `_stream_ai_response`

原流程：
```
query → dify_client.chat_stream(query, user_id, conversation_id, inputs) → SSE
```

新流程：
```
query → intent_classifier.classify(query)
  ├── greeting  → 固定回复文本
  ├── chitchat  → llm_service.chat(闲聊 prompt, 无 context)
  ├── kb_query  → knowledge_service.retrieve(query)
  │                → llm_service.chat(RAG prompt, 带 context + sources)
  └── transfer  → 固定回复 + 触发状态机 escalate
```

SSE 事件格式保持不变（`event: message`, `event: message_end`, `event: done`），前端零改动。

#### 2.4 清理

- 移除 `app/services/dify_client.py`
- 清理 `app/config.py` 中 `dify_*` 配置项
- 移除 `app/models/knowledge.py` 中的 `CollegeDataset` 模型
- `kb_entries` 表正式移除 `dify_document_id`、`dify_dataset_id` 字段

---

### 阶段 3：清理与优化

- 从 `deploy/docker-compose.yml` 中移除 Dify 相关配置
- 更新 `deploy/nginx/gateway.conf`（移除 `/dify/` 代理规则）
- 更新部署文档
- 性能调优：
  - embedding 结果缓存（Redis，避免重复计算）
  - 检索结果缓存（相同 query 短期内复用）
  - 连接池优化（通义千问 HTTP 客户端复用）
- 监控：
  - 记录每次 LLM 调用的 token 消耗和响应时间
  - 接入 `chat_analytics` 表（R05 需求 2）

---

## 四、关键技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| LLM | 通义千问 qwen-plus (云端) | 与当前 Dify 配置一致，无迁移风险 |
| Embedding | 通义千问 text-embedding-v3 | 替代 multimodal-embedding-v1，效果更好且更便宜 |
| Rerank | 通义千问 qwen3-rerank (可选) | 当前 Dify 已在用，效果验证过 |
| 向量存储 | PG pgvector 扩展 | 复用现有 PG，零额外部署成本 |
| 流式输出 | 通义千问 SSE / OpenAI 兼容接口 | 替代 Dify SSE，前端 SSE 协议不变 |

---

## 五、对 kb-pipeline 的影响

kb-pipeline 的数据清洗流程**不需要任何改动**。产出的 MD 文件是通用的：
- 阶段 0：通过 Dify Dataset API 入库（现有 `scripts/migrate_kb.py`）
- 阶段 1+：通过新的 `scripts/import_kb_v2.py` 入库（embedding → pgvector）

`kb-pipeline/KB-SPEC.md` 中的第八节"Dify 入库配置"需要在阶段 1 完成后更新为"自建入库配置"。

---

## 六、风险与应对

| 风险 | 应对 |
|------|------|
| 自建 RAG 效果不如 Dify | 阶段 1 两套并存对比，验证通过再切换 |
| 通义千问 API 变更/限流 | LLM 服务层做成可插拔接口，支持切换其他供应商 |
| 意图分类准确率下降 | 复用 Dify 现有 prompt，本质是同一个模型同一个 prompt |
| pgvector 性能不足 | 当前数据量 1000 级别，pgvector 绰绰有余；万级以上可迁移 Qdrant |
| 多轮对话上下文丢失 | 从 PG messages 表取最近 N 条历史，与 Dify 的 memory window 等价 |

---

## 七、关联文档

| 文档 | 位置 | 说明 |
|------|------|------|
| Dify Chatflow 设计 | `docs/design/dify-chatflow-design.md` | 当前 Dify 配置详情（迁移参考） |
| KB 增强需求 | `docs/requirements/R05-KB-增强需求.md` | 图文教程、无答案统计等需求 |
| KB 规范 | `kb-pipeline/KB-SPEC.md` | V2 知识库数据规范 |
| 现有迁移脚本 | `scripts/migrate_kb.py` | 阶段 0 使用的 Dify 入库脚本 |
| Dify 环境信息 | `services/gateway/.env` | 当前 Dify API Key 和 Dataset ID |
| Chatflow YAML | `deploy/dify/yixiaoguan-chatflow.yml` | 意图分类 prompt 和 RAG prompt 的源文件 |

---

*方案版本：v1.0*
*确认日期：2026-04-16*
*执行时机：阶段 0（KB 数据清洗）完成后启动阶段 1*
