# Dify Chatflow 设计文档

> 来源：2026-04-14 审查 Dify 实际配置后整理
> 状态：**当前架构记录 + 扩展规划**

---

## 一、当前架构

### Chatflow 名称：医小管-主对话流

### 节点结构

```
开始
  → 意图分类 (qwen-plus)
       ├─ 闲聊/greeting → 闲聊LLM (qwen-plus) → 闲聊输出 (文本)
       ├─ kb_query      → 知识检索 → RAG检索 (global-kb) → 知识检索输出 (qwen-plus → 文本)
       ├─ transfer       → 转人工回复 (固定文本)
       └─ （其他）       → 兜底处理
```

### 意图分类器配置

- **模型**：qwen-plus
- **分类**：闲聊、greeting(打招呼)、出发点、意义点、kb_query(知识库查询)、投诉点、transfer(转人工/T1)

### RAG 检索配置

- **数据集**：global-kb (ec072e85-ebb3-4f2a-a966-a21566b88995)
- **Embedding**：multimodal-embedding-v1（通义千问）
- **检索方式**：semantic_search + qwen3-rerank
- **Top K**：3
- **Score 阈值**：0.5（未启用）

### Gateway 调用方式

```python
# services/gateway/app/services/dify_client.py
payload = {
    "inputs": inputs or {},    # ← 这里传用户上下文
    "query": query,
    "response_mode": "streaming",
    "user": user_id,
}
if conversation_id:
    payload["conversation_id"] = conversation_id

# POST {dify_api_url}/chat-messages (SSE streaming)
```

---

## 二、已确认的扩展（不加新分支）

以下功能**均不需要修改 Chatflow 分支结构**：

### 2.1 学院个性化（改 inputs）

```python
# Gateway 传入：
inputs = {
    "college_name": "临床与基础医学院",
    "campus": "济南校区",
}
```

Dify 知识检索输出节点的 prompt 增加：
```
该学生来自{{college_name}}（{{campus}}），请优先使用与其学院相关的信息回答。
如果检索结果中有与该学生学院直接相关的内容，优先引用。
```

### 2.2 Top 10 图文教程（KB 内容 + 前端）

KB 段落中包含特殊标记，Dify 原样输出，前端解析渲染：
```markdown
## 电费缴纳操作步骤

1. 打开"完美校园"APP → 底部第三个Tab"校园卡"
2. 点击右上角"电费充值"
3. 选择校区 → 楼栋 → 房间号
4. 输入金额 → 支付

[tutorial:electricity-payment]
```

### 2.3 教师定制通知（Gateway 拦截，不进 Dify）

```python
# Gateway chat 路由伪代码：
async def send_message(user, query):
    # Step 1: 检查是否有活跃通知
    announcement = await check_announcements(user.college_id, user.class_id)
    if announcement:
        return stream_announcement(announcement)
    
    # Step 2: 正常走 Dify
    return dify_client.chat_stream(query, user.id, ...)
```

### 2.4 高频无答案统计（Gateway 后处理，不改 Dify）

```python
# Gateway 解析 Dify SSE 事件：
async for event in dify_stream:
    if event["event"] == "message_end":
        metadata = event.get("metadata", {})
        await save_chat_analytics(
            query=original_query,
            rag_score=extract_rag_score(metadata),
            is_answered=True,
        )
```

---

## 三、可能的未来扩展（需要改 Dify）

以下是**未来可能**需要修改 Chatflow 的场景，目前不做：

| 场景 | 改动 | 时机 |
|------|------|------|
| AI 主动判断需要转人工（置信度低时自动触发） | 在 RAG 输出后加条件分支 | 有足够数据验证阈值后 |
| 多轮追问（AI 追问用户以明确需求） | Chatflow 加迭代节点 | 二期 |
| 多语言支持 | 意图分类加语言检测 | 有需求时 |

---

## 四、环境信息

| 项目 | 值 |
|------|---|
| Dify 地址 | http://192.168.100.165:3000 |
| Dify API (v1) | http://192.168.100.165:3000/v1 |
| Chat API Key | app-WyMuIbnBB351RxqitjbncX6A |
| Dataset API Key | dataset-XcnM3rGW1vBpBk9yQxXC5jCo |
| 旧 Dataset ID | ec072e85-ebb3-4f2a-a966-a21566b88995 (global-kb, 432 docs) |
| 新 Dataset | 待创建 (global-kb-v2) |
| Workspace | easten's Workspace |

---

*创建日期：2026-04-14*
*基于 Dify 实际配置截图 + API 审查*
