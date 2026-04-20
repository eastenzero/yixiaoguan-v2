# Dify LLM 节点配置一览（2026-04-20）

> 来源：SSH 直连 Dify PostgreSQL (`docker-db_postgres-1`) 只读查询 `workflows.graph`
> 应用：医小管-主对话流（`8cfaee92-f95c-4316-80a4-ab5d93614772`）

## 1. LLM / Question Classifier 节点参数表

| 节点 | 类型 | 模型 | 模式 | 温度 | max_tokens | top_p | 其他 |
|------|------|------|------|------|-----------|-------|------|
| 意图分类 | Question Classifier | qwen-plus (tongyi) | chat | 0.1 | — | — | 查询变量: sys.query |
| 闲聊LLM | LLM | qwen-plus (tongyi) | chat | 0.7 | — | — | 上下文: 禁用 |
| RAG 回答 | LLM | qwen-plus (tongyi) | chat | 0.7 | — | — | 上下文: 启用 (知识检索.result) |

## 2. 知识检索节点参数表

| 节点 | 检索模式 | Dataset ID (草稿) | Dataset ID (已发布) | Top K | Reranking | Rerank 模型 |
|------|---------|------------------|---------------------|-------|-----------|-------------|
| 知识检索 | multiple | `4db0c819-7847-4a95-bf06-5b73a9d41d70` | `ec072e85-ebb3-4f2a-a966-a21566b88995` | 4 | 启用 | qwen3-rerank (tongyi) |

## 3. 固定文本节点一览

| 节点 | 输出类型 | 内容摘要 |
|------|---------|---------|
| 问候回复 | 固定文本 | "你好！我是医小管 🏥 ..." |
| 闲聊输出 | 变量引用 | `{{#1000000000020.text#}}`（闲聊LLM 输出） |
| 知识回答输出 | 变量引用 | `{{#1000000000031.text#}}`（RAG 回答输出） |
| 转人工回复 | 固定文本 | "我已收到你的转人工请求..." |

## 4. 与 R06-1' 预期对比

| 节点 | 当前模型 | R06-1' 预期 | 当前温度 | R06-1' 建议 | 结论 |
|------|---------|------------|---------|------------|------|
| 意图分类 | qwen-plus | qwen-turbo | 0.1 | 0.1 | ⚠️ 模型超预期（成本略高） |
| kb_query 最终回复 | qwen-plus | qwen-plus | 0.7 | 0.3 | ⚠️ 温度偏高 |
| chitchat 闲聊 | qwen-plus | qwen-plus / qwen-turbo | 0.7 | 0.7 | ✅ 符合 |
| transfer | — | — | — | — | 固定文本，无 LLM |

> **建议**：意图分类可降级为 qwen-turbo 节省成本；RAG 回答温度建议从 0.7 调至 0.3。

---

*本文档为 R06-3a / R06-1' Scout 共用产出，严格只读。*
