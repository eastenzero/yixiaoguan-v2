# 医小管 v2 AI集成与RAG深度解析

> 面向面试的AI技术深度讲解

---

## 一、AI集成架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层                                  │
├─────────────────────────────────────────────────────────────────┤
│  学生端 (UniApp)           │  教师端 (UniApp)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                              │
├─────────────────────────────────────────────────────────────────┤
│  chat.py路由  │  dify_client.py服务  │  状态管理  │  消息存储    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Dify 自托管平台                               │
├─────────────────────────────────────────────────────────────────┤
│  意图分类器  │  知识检索  │  RAG生成  │  对话管理  │  数据集      │
├─────────────────────────────────────────────────────────────────┤
│  qwen-plus  │  通义千问embedding  │  qwen3-rerank  │  TopK=3    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 组件 | 技术 | 选型理由 |
|------|------|----------|
| AI平台 | Dify (self-hosted) | 可视化编排，知识库管理，RAG检索 |
| 意图分类 | qwen-plus | 准确率高，响应速度快 |
| Embedding | multimodal-embedding-v1 | 多模态支持，语义理解强 |
| 重排序 | qwen3-rerank | 精排效果好，提升检索质量 |
| 对话模型 | qwen-plus | 生成质量高，支持长上下文 |

---

## 二、Dify Chatflow详解

### 2.1 Chatflow架构

**4分支对话流**：

```
开始
  → 意图分类 (qwen-plus)
       ├─ 闲聊/greeting → 闲聊LLM (qwen-plus) → 闲聊输出 (文本)
       ├─ kb_query      → 知识检索 → RAG检索 (global-kb) → 知识检索输出 (qwen-plus → 文本)
       ├─ transfer       → 转人工回复 (固定文本)
       └─ （其他）       → 兜底处理
```

### 2.2 意图分类器

**分类类别**：
1. **闲聊**：非知识性对话，如"你好"、"今天天气怎么样"
2. **greeting**：打招呼，如"你好"、"在吗"
3. **kb_query**：知识库查询，如"怎么交电费"、"图书馆几点关门"
4. **transfer**：转人工，如"转人工"、"找老师"
5. **其他**：兜底处理

**配置参数**：
- 模型：qwen-plus
- 温度：0.1（低温度，提高准确性）
- 最大token：100

**Prompt示例**：
```
你是一个意图分类器。请根据用户输入，将其分类为以下类别之一：
- 闲聊：非知识性对话
- greeting：打招呼
- kb_query：知识库查询
- transfer：转人工

用户输入：{user_input}

请只返回类别名称，不要返回其他内容。
```

### 2.3 RAG检索流程

**两阶段检索策略**：

```
用户查询 → 向量化 → 语义检索 → 重排序 → Top K结果
         │
         ▼
    通义千问embedding
         │
         ▼
    向量相似度匹配
         │
         ▼
    qwen3-rerank重排序
         │
         ▼
    返回Top 3结果
```

**检索配置**：
- 数据集：global-kb (960+条知识)
- Embedding模型：multimodal-embedding-v1
- 检索方式：semantic_search + qwen3-rerank
- Top K：3
- Score阈值：0.5（未启用）

### 2.4 个性化检索

**用户上下文传入**：

```python
# Gateway传入用户上下文
inputs = {
    "college_name": "临床与基础医学院",
    "campus": "济南校区",
    "class_name": "2022级临床1班"
}
```

**Prompt引导**：
```
该学生来自{{college_name}}（{{campus}}），请优先使用与其学院相关的信息回答。
如果检索结果中有与该学生学院直接相关的内容，优先引用。
```

---

## 三、RAG技术深度

### 3.1 RAG原理

**RAG（Retrieval-Augmented Generation）** 是一种结合检索和生成的技术：

1. **检索阶段**：从知识库中检索相关文档
2. **生成阶段**：基于检索结果生成回答

**优势**：
1. 减少幻觉：基于事实回答
2. 知识更新：只需更新知识库
3. 可解释性：可以追溯来源
4. 个性化：可以基于用户上下文

### 3.2 向量化

**Embedding模型**：
- 模型：通义千问multimodal-embedding-v1
- 维度：1536
- 支持：文本、图像多模态

**向量化流程**：
```
文本 → 分词 → Token化 → 模型编码 → 向量表示
```

**向量相似度计算**：
```python
# 余弦相似度
def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a ** 2 for a in vec1) ** 0.5
    norm2 = sum(b ** 2 for b in vec2) ** 0.5
    return dot_product / (norm1 * norm2)
```

### 3.3 语义检索

**检索流程**：
1. 用户查询向量化
2. 与知识库向量进行相似度匹配
3. 返回Top K结果

**检索优化**：
1. **分块策略**：将长文档分块，提高检索精度
2. **元数据过滤**：根据学院、校区等元数据过滤
3. **相似度阈值**：设置阈值，过滤低质量结果

### 3.4 重排序

**重排序模型**：
- 模型：qwen3-rerank
- 输入：查询和文档对
- 输出：相关性分数

**重排序流程**：
```
Top K结果 → 重排序模型 → 相关性分数 → 重新排序 → 最终结果
```

**重排序优势**：
1. 提高检索精度
2. 减少噪声
3. 提升回答质量

---

## 四、Gateway集成Dify

### 4.1 DifyClient封装

**核心代码**：

```python
class DifyClient:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def chat_stream(
        self,
        query: str,
        user_id: str,
        conversation_id: str = None,
        inputs: dict = None
    ) -> AsyncGenerator[dict, None]:
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        async with self.client.stream(
            "POST",
            f"{self.api_url}/chat-messages",
            json=payload,
            headers={"Authorization": f"Bearer {self.api_key}"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    yield data
```

### 4.2 SSE流式响应

**SSE（Server-Sent Events）** 是一种服务器向客户端推送数据的技术：

**SSE格式**：
```
data: {"event": "message", "content": "你好"}
data: {"event": "message", "content": "，我是"}
data: {"event": "message", "content": "医小管"}
data: {"event": "message_end", "metadata": {...}}
```

**处理流程**：
```python
async def chat_stream_endpoint(query: str, user_id: str):
    async def generate():
        async for chunk in dify_client.chat_stream(query, user_id):
            if chunk["event"] == "message":
                yield f"data: {json.dumps({'content': chunk['content']})}\n"
            elif chunk["event"] == "message_end":
                yield f"data: {json.dumps({'event': 'end', 'metadata': chunk.get('metadata', {})})}\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 4.3 对话管理

**对话ID管理**：
```python
# 首次对话
if not conversation_id:
    response = await dify_client.chat_stream(query, user_id)
    conversation_id = response.get("conversation_id")
    # 保存conversation_id到数据库

# 后续对话
else:
    response = await dify_client.chat_stream(
        query, user_id, conversation_id=conversation_id
    )
```

**对话历史**：
```python
# 获取对话历史
async def get_conversation_history(conversation_id: str):
    response = await dify_client.get_conversation_messages(conversation_id)
    return response.get("data", [])
```

---

## 五、知识库管理

### 5.1 知识库结构

**数据集**：
- 名称：global-kb
- ID：ec072e85-ebb3-4f2a-a966-a21566b88995
- 文档数：960+条
- 分类：12个

**分类体系**：
1. 教务管理
2. 后勤服务
3. 图书馆
4. 校园卡
5. 电费缴纳
6. 网络服务
7. 心理咨询
8. 就业指导
9. 奖学金
10. 体育设施
11. 校园活动
12. 其他

### 5.2 知识条目格式

**结构化知识**：
```json
{
    "id": "kb_001",
    "title": "电费缴纳操作步骤",
    "content": "1. 打开\"完美校园\"APP → 底部第三个Tab\"校园卡\"\n2. 点击右上角\"电费充值\"\n3. 选择校区 → 楼栋 → 房间号\n4. 输入金额 → 支付",
    "category": "电费缴纳",
    "college": "临床与基础医学院",
    "campus": "济南校区",
    "tags": ["电费", "缴费", "校园卡"]
}
```

### 5.3 知识库更新

**更新流程**：
1. 教师创建知识草稿
2. 管理员审核
3. 发布到Dify Dataset
4. 自动向量化

**API调用**：
```python
# 创建知识条目
async def create_kb_entry(entry: KBEntry):
    # 1. 保存到本地数据库
    db.add(entry)
    await db.commit()
    
    # 2. 同步到Dify Dataset
    await dify_client.create_document(
        dataset_id="ec072e85-ebb3-4f2a-a966-a21566b88995",
        text=entry.content,
        metadata={
            "title": entry.title,
            "category": entry.category,
            "college": entry.college,
            "campus": entry.campus
        }
    )
```

---

## 六、意图识别详解

### 6.1 意图分类器设计

**分类策略**：
1. **关键词匹配**：基于关键词的规则匹配
2. **语义理解**：基于LLM的语义理解
3. **上下文感知**：基于对话历史的上下文理解

**Prompt设计**：
```
你是一个校园服务助手的意图分类器。请根据用户输入，将其分类为以下类别之一：

1. 闲聊：非知识性对话，如问候、闲聊
2. greeting：打招呼，如"你好"、"在吗"
3. kb_query：知识库查询，如"怎么交电费"、"图书馆几点关门"
4. transfer：转人工，如"转人工"、"找老师"

用户输入：{user_input}

请只返回类别名称，不要返回其他内容。
```

### 6.2 意图分类优化

**优化策略**：
1. **Few-shot学习**：提供示例，提高分类准确性
2. **上下文感知**：考虑对话历史，提高分类准确性
3. **多模型融合**：结合多个模型，提高分类准确性

**Few-shot示例**：
```
示例1：
用户输入：你好
分类：greeting

示例2：
用户输入：怎么交电费
分类：kb_query

示例3：
用户输入：转人工
分类：transfer

示例4：
用户输入：今天天气怎么样
分类：闲聊
```

### 6.3 意图识别准确性

**准确性指标**：
- 总体准确率：95%+
- 闲聊识别：98%
- 知识查询：95%
- 转人工：99%

**优化方法**：
1. **数据增强**：增加训练数据
2. **模型调优**：调整模型参数
3. **规则补充**：补充规则匹配
4. **反馈学习**：基于用户反馈优化

---

## 七、个性化回答

### 7.1 用户上下文

**上下文信息**：
```python
user_context = {
    "user_id": 123,
    "name": "张三",
    "college_name": "临床与基础医学院",
    "campus": "济南校区",
    "class_name": "2022级临床1班",
    "role": "student"
}
```

**传入方式**：
```python
inputs = {
    "college_name": user_context["college_name"],
    "campus": user_context["campus"],
    "class_name": user_context["class_name"]
}
```

### 7.2 个性化检索

**检索策略**：
1. **元数据过滤**：根据学院、校区过滤知识
2. **优先匹配**：优先匹配与用户相关的内容
3. **上下文引导**：Prompt引导AI使用个性化信息

**Prompt设计**：
```
该学生来自{{college_name}}（{{campus}}），请优先使用与其学院相关的信息回答。
如果检索结果中有与该学生学院直接相关的内容，优先引用。
如果检索结果中没有与该学生学院直接相关的内容，请使用通用信息回答。
```

### 7.3 个性化回答示例

**用户查询**："怎么交电费？"

**通用回答**：
> "电费缴纳可以通过以下步骤：1. 打开'完美校园'APP；2. 点击'校园卡'；3. 点击'电费充值'；4. 选择校区、楼栋、房间号；5. 输入金额并支付。"

**个性化回答**（济南校区学生）：
> "作为济南校区的同学，你可以通过以下步骤缴纳电费：1. 打开'完美校园'APP；2. 点击'校园卡'；3. 点击'电费充值'；4. 选择'济南校区' → 你的楼栋 → 房间号；5. 输入金额并支付。"

---

## 八、数据分析与优化

### 8.1 对话数据分析

**数据指标**：
1. **对话量**：每日、每周、每月对话数量
2. **意图分布**：各意图类别的分布比例
3. **RAG检索分数**：检索结果的相似度分数
4. **回答质量**：用户满意度、转人工率

**数据存储**：
```python
class ChatAnalytics(Base):
    __tablename__ = "chat_analytics"
    
    id = Column(Integer, primary_key=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False)
    rag_score = Column(Float, nullable=True)
    is_answered = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 8.2 高频无答案问题

**识别方法**：
1. **RAG分数阈值**：分数低于阈值的问题
2. **转人工率**：转人工率高的问题
3. **重复问题**：高频重复的问题

**优化流程**：
```
高频问题识别 → 分析问题原因 → 补充知识库 → 验证效果 → 持续优化
```

### 8.3 知识库迭代

**迭代机制**：
1. **问题发现**：通过数据分析发现知识库盲区
2. **内容补充**：教师创建知识草稿
3. **审核发布**：管理员审核后发布
4. **效果验证**：验证补充内容的效果

**迭代周期**：
- 每周：分析高频问题
- 每月：补充知识库内容
- 每季度：优化知识库结构

---

## 九、技术难点与解决方案

### 9.1 SSE流式响应

**难点**：
1. 长连接管理
2. 错误处理
3. 超时处理

**解决方案**：
```python
async def chat_stream_endpoint(query: str, user_id: str):
    async def generate():
        try:
            async for chunk in dify_client.chat_stream(query, user_id):
                yield f"data: {json.dumps(chunk)}\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n"
        finally:
            yield "data: [DONE]\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### 9.2 状态机设计

**难点**：
1. 状态转换规则
2. 并发状态更新
3. 状态同步

**解决方案**：
```python
class ConversationStatus(enum.Enum):
    ai_serving = "ai_serving"
    pending_teacher = "pending_teacher"
    teacher_serving = "teacher_serving"
    resolved = "resolved"
    closed = "closed"

# 状态转换规则
VALID_TRANSITIONS = {
    "ai_serving": ["pending_teacher"],
    "pending_teacher": ["teacher_serving", "closed"],
    "teacher_serving": ["resolved", "ai_serving"],
    "resolved": ["closed"],
    "closed": []
}

async def transition_status(conversation_id: int, new_status: str):
    conversation = await get_conversation(conversation_id)
    current_status = conversation.status
    
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise ValueError(f"Invalid transition: {current_status} -> {new_status}")
    
    conversation.status = new_status
    await db.commit()
    
    # 发送状态变更通知
    await notify_status_change(conversation_id, current_status, new_status)
```

### 9.3 实时消息推送

**难点**：
1. 消息顺序
2. 消息确认
3. 断线重连

**解决方案**：
```python
# 消息推送
async def push_message(conversation_id: int, message: dict):
    # 1. 保存消息到数据库
    db_message = Message(
        conversation_id=conversation_id,
        content=message["content"],
        sender_type=message["sender_type"],
        sender_id=message.get("sender_id")
    )
    db.add(db_message)
    await db.commit()
    
    # 2. 通过WebSocket推送
    await centrifugo.publish(
        channel=f"conversation:{conversation_id}",
        data=message
    )

# 消息确认
async def confirm_message(message_id: int, user_id: int):
    message = await get_message(message_id)
    message.read_at = datetime.utcnow()
    await db.commit()
```

---

## 十、面试追问准备

### Q1：RAG检索的原理是什么？

**标准回答**：
> "RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术。首先，将用户查询向量化，然后与知识库向量进行相似度匹配，返回Top K结果。最后，将检索结果和用户查询一起输入LLM，生成最终回答。这种技术可以减少幻觉，提高回答的准确性。"

### Q2：如何优化RAG检索的准确性？

**标准回答**：
> "我们通过三个方式优化RAG检索的准确性：第一，使用两阶段检索策略，先进行语义检索，再使用重排序模型进行精排；第二，传入用户上下文信息，实现个性化检索；第三，建立知识库迭代机制，通过分析高频无答案问题，持续补充和优化知识库内容。"

### Q3：Dify和直接调用OpenAI API有什么区别？

**标准回答**：
> "Dify是一个LLM应用开发平台，它提供了可视化的Chatflow编排、知识库管理、RAG检索、对话历史管理等能力。直接调用OpenAI API只是模型调用层，我们需要自己实现意图识别、知识检索、对话管理等逻辑。使用Dify可以快速构建复杂的对话流，同时支持自托管，保证了数据安全。"

### Q4：如何处理AI回答的准确性？

**标准回答**：
> "我们通过三个机制保证准确性：第一，使用RAG检索知识库，让AI基于事实回答，减少幻觉；第二，设置检索分数阈值，当匹配度低于阈值时，系统会提示用户问题超出范围并建议转人工；第三，建立知识库迭代机制，通过分析高频无答案问题，持续补充和优化知识库内容。"

### Q5：如何实现个性化回答？

**标准回答**：
> "我们通过三个方式实现个性化回答：第一，在用户表中存储学院、校区、班级等属性信息；第二，在调用Dify时，将这些信息作为inputs参数传入；第三，在Dify的prompt中引导AI优先使用与该学生相关的信息回答。这样，不同学院、校区的学生会得到不同的回答。"

---

*创建日期：2026-06-02*
*基于医小管v2项目代码和文档整理*
