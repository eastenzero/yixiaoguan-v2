# 医小管 v2 技术架构深度解析

> 面向面试的技术架构详解

---

## 一、整体架构设计

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层                                  │
├─────────────────────────────────────────────────────────────────┤
│  学生端 (UniApp)           │  教师端 (UniApp)                   │
│  ├─ 微信小程序              │  ├─ 微信小程序                      │
│  └─ H5                    │  └─ H5                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      网关层 (Nginx)                              │
├─────────────────────────────────────────────────────────────────┤
│  负载均衡  │  SSL终止  │  静态资源  │  API路由                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    应用层 (FastAPI Gateway)                      │
├─────────────────────────────────────────────────────────────────┤
│  认证模块  │ 会话模块 │ 消息模块 │ 知识库模块 │ 管理后台 │ 数据分析 │
├─────────────────────────────────────────────────────────────────┤
│                SQLAlchemy (async) + Alembic                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据层                                      │
├─────────────────────────────────────────────────────────────────┤
│         PostgreSQL 15+              Redis 7+                   │
│         (主数据库)                 (缓存/会话)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI引擎层                                   │
├─────────────────────────────────────────────────────────────────┤
│                    Dify 自托管平台                               │
│  ├─ Chatflow编排  ├─ 知识库管理  ├─ RAG检索  ├─ 对话管理        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型矩阵

| 层 | 技术 | 选型理由 |
|---|------|---------|
| 前端 | UniApp + Vue 3 | 跨平台复用，微信小程序+H5双端 |
| 网关 | Nginx | 高性能反向代理，负载均衡 |
| 后端 | FastAPI | 异步原生，类型注解，自动文档 |
| ORM | SQLAlchemy (async) | 异步支持，类型安全，迁移管理 |
| 数据库 | PostgreSQL 15+ | 功能强大，性能优秀，扩展性好 |
| 缓存 | Redis 7+ | 高性能缓存，会话管理 |
| AI引擎 | Dify (self-hosted) | 可视化编排，知识库管理，RAG检索 |
| 部署 | Docker Compose | 容器化部署，环境一致性 |

---

## 二、后端架构详解

### 2.1 FastAPI应用结构

```
services/gateway/app/
├── main.py                 # 应用入口，路由注册
├── config.py              # 配置管理
├── database.py            # 数据库连接
├── models/                # 数据模型
│   ├── user.py           # 用户模型
│   ├── conversation.py   # 会话模型
│   ├── knowledge.py      # 知识库模型
│   └── ...
├── routers/               # 路由模块
│   ├── auth.py           # 认证路由
│   ├── chat.py           # 聊天路由
│   ├── conversations.py  # 会话路由
│   └── ...
├── schemas/               # Pydantic模型
├── services/              # 业务逻辑
└── utils/                 # 工具函数
```

### 2.2 核心路由模块

| 模块 | 功能 | 技术亮点 |
|------|------|----------|
| auth.py | 用户认证 | JWT token、微信登录 |
| chat.py | AI对话 | SSE流式响应、Dify集成 |
| conversations.py | 会话管理 | 状态机、分页查询 |
| ws.py | WebSocket | 实时通信、房间管理 |
| knowledge.py | 知识库 | CRUD、批量操作 |
| admin.py | 管理后台 | 权限控制、数据导出 |
| analytics.py | 数据分析 | 统计查询、数据可视化 |

### 2.3 异步架构实现

**FastAPI异步处理流程**：

```python
# 1. 异步路由处理
@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    # 2. 异步数据库操作
    user = await db.get(User, request.user_id)
    
    # 3. 异步HTTP请求
    async with httpx.AsyncClient() as client:
        response = await client.post(dify_url, json=payload)
    
    # 4. 异步生成器处理SSE
    async def generate():
        async for chunk in response.aiter_text():
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**SQLAlchemy异步会话**：

```python
# 异步会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession)

# 异步依赖注入
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# 异步查询
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

---

## 三、数据库设计

### 3.1 核心表结构

**用户表 (users)**：
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    staff_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role userrole NOT NULL,
    college_id INTEGER REFERENCES colleges(id),
    class_id INTEGER REFERENCES classes(id),
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(512),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**会话表 (conversations)**：
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) NOT NULL,
    teacher_id INTEGER REFERENCES users(id),
    status conversationstatus NOT NULL,
    dify_conversation_id VARCHAR(128),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    last_read_at TIMESTAMP
);

-- 索引优化
CREATE INDEX idx_conversations_student ON conversations(student_id);
CREATE INDEX idx_conversations_status ON conversations(status);
```

**消息表 (messages)**：
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) NOT NULL,
    sender_type sendertype NOT NULL,
    sender_id INTEGER REFERENCES users(id),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(conversation_id, created_at);
```

### 3.2 索引优化策略

1. **用户表索引**：
   - `staff_id` 唯一索引，加速登录查询
   - `college_id` 外键索引，加速学院关联查询

2. **会话表索引**：
   - `student_id` 索引，加速用户会话查询
   - `status` 索引，加速状态筛选
   - `(student_id, updated_at)` 联合索引，优化分页查询

3. **消息表索引**：
   - `conversation_id` 索引，加速会话消息查询
   - `(conversation_id, created_at)` 联合索引，优化时间排序

### 3.3 数据库迁移

**Alembic迁移管理**：

```bash
# 创建迁移脚本
alembic revision --autogenerate -m "add_user_table"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

**迁移最佳实践**：
1. 每次迁移只做一件事
2. 迁移脚本要有明确的命名
3. 测试环境先验证迁移
4. 生产环境备份后执行

---

## 四、AI引擎架构

### 4.1 Dify Chatflow设计

**4分支对话流架构**：

```
开始
  → 意图分类 (qwen-plus)
       ├─ 闲聊/greeting → 闲聊LLM (qwen-plus) → 闲聊输出 (文本)
       ├─ kb_query      → 知识检索 → RAG检索 (global-kb) → 知识检索输出 (qwen-plus → 文本)
       ├─ transfer       → 转人工回复 (固定文本)
       └─ （其他）       → 兜底处理
```

**意图分类器配置**：
- 模型：qwen-plus
- 分类：闲聊、greeting、kb_query、transfer等
- 准确率：95%+

### 4.2 RAG检索流程

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

**检索优化**：
1. **向量化**：使用通义千问multimodal-embedding-v1模型
2. **语义检索**：基于向量相似度的语义匹配
3. **重排序**：使用qwen3-rerank对结果进行重排序
4. **个性化**：传入用户学院、校区等上下文，优先匹配相关内容

### 4.3 Gateway调用Dify

**SSE流式响应处理**：

```python
async def chat_stream(query: str, user_id: str, conversation_id: str = None):
    payload = {
        "inputs": inputs or {},
        "query": query,
        "response_mode": "streaming",
        "user": user_id,
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{dify_api_url}/chat-messages",
            json=payload,
            headers={"Authorization": f"Bearer {dify_api_key}"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    yield data
```

---

## 五、实时通信架构

### 5.1 WebSocket协议选型

**技术选型**：
- 协议：WebSocket
- 服务端：Centrifugo
- 客户端：UniApp WebSocket API

**选型理由**：
1. **Centrifugo优势**：
   - 支持集群部署
   - 消息持久化
   - 断线重连
   - 房间广播

2. **WebSocket优势**：
   - 全双工通信
   - 低延迟
   - 实时性好

### 5.2 会话状态机

**5种会话状态**：

```
┌─────────────────────────────────────────────────────────────┐
│                    会话状态机                                │
├─────────────────────────────────────────────────────────────┤
│  ai_serving → pending_teacher → teacher_serving → resolved → closed
│      │              │                │                      │
│      │              │                │                      │
│      ▼              ▼                ▼                      │
│  AI自动服务    等待教师接入      教师服务中              会话关闭
└─────────────────────────────────────────────────────────────┘
```

**状态转换规则**：
1. `ai_serving → pending_teacher`：学生请求转人工
2. `pending_teacher → teacher_serving`：教师接单
3. `teacher_serving → resolved`：问题解决
4. `resolved → closed`：会话关闭
5. `teacher_serving → ai_serving`：教师退出，恢复AI服务

### 5.3 消息推送机制

**消息类型**：
1. **学生消息**：学生发送给AI或教师
2. **AI回复**：AI生成的回答
3. **教师消息**：教师发送给学生
4. **系统消息**：状态变更通知

**推送流程**：

```python
# 1. 学生发送消息
async def send_message(student_id: int, content: str):
    conversation = await get_active_conversation(student_id)
    
    if conversation.status == "ai_serving":
        # 调用Dify，流式返回AI回复
        async for chunk in dify_client.chat_stream(content):
            await send_to_student(student_id, chunk)
    
    elif conversation.status == "teacher_serving":
        # 通过WebSocket推送给教师
        await send_to_teacher(conversation.teacher_id, {
            "type": "student_message",
            "content": content,
            "conversation_id": conversation.id
        })
```

---

## 六、缓存架构

### 6.1 Redis使用场景

| 场景 | 数据结构 | 过期时间 | 说明 |
|------|----------|----------|------|
| 用户会话 | String | 24小时 | JWT token缓存 |
| 验证码 | String | 5分钟 | 短信验证码 |
| 热点数据 | Hash | 1小时 | 用户信息、配置 |
| 排行榜 | Sorted Set | 永久 | 知识库热度 |
| 限流 | String | 1分钟 | API限流计数 |

### 6.2 缓存策略

**缓存穿透防护**：

```python
async def get_user(user_id: int):
    # 1. 先查缓存
    cache_key = f"user:{user_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 2. 缓存未命中，查数据库
    user = await db.get(User, user_id)
    if not user:
        # 3. 缓存空值，防止穿透
        await redis.setex(cache_key, 300, "null")
        return None
    
    # 4. 写入缓存
    await redis.setex(cache_key, 3600, json.dumps(user.to_dict()))
    return user
```

**缓存更新策略**：
1. **Cache-Aside**：先更新数据库，再删除缓存
2. **Write-Behind**：异步更新缓存
3. **Read-Through**：缓存未命中时自动加载

---

## 七、部署架构

### 7.1 Docker Compose编排

```yaml
version: '3.8'
services:
  gateway:
    build: ./services/gateway
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - REDIS_URL=redis://redis:6379
      - DIFY_API_URL=http://dify:3000/v1
    depends_on:
      - postgres
      - redis
      - dify
  
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=yixiaoguan
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  dify:
    image: langgenius/dify-api:latest
    ports:
      - "3000:3000"
    environment:
      - SECRET_KEY=your-secret-key
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - gateway

volumes:
  postgres_data:
  redis_data:
```

### 7.2 环境配置管理

**配置分层**：
1. **默认配置**：config.py中的默认值
2. **环境变量**：.env文件中的配置
3. **运行时配置**：Docker Compose环境变量

**配置示例**：

```python
# config.py
class Settings:
    database_url: str = "postgresql://user:pass@localhost:5432/db"
    redis_url: str = "redis://localhost:6379"
    dify_api_url: str = "http://localhost:3000/v1"
    dify_api_key: str = ""
    secret_key: str = ""
    
    class Config:
        env_file = ".env"
```

---

## 八、监控与日志

### 8.1 健康检查

**健康检查端点**：

```python
@app.get("/health")
async def health(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    checks = {}
    
    # PostgreSQL检查
    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {e}"
    
    # Redis检查
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
    
    # Dify检查
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{dify_api_url}/parameters")
            checks["dify"] = "ok" if resp.status_code < 500 else f"error: {resp.status_code}"
    except Exception as e:
        checks["dify"] = f"error: {e}"
    
    return {"status": "ok" if all(v == "ok" for v in checks.values()) else "degraded", "checks": checks}
```

### 8.2 日志管理

**日志级别**：
1. **DEBUG**：调试信息
2. **INFO**：正常操作
3. **WARNING**：警告信息
4. **ERROR**：错误信息
5. **CRITICAL**：严重错误

**日志格式**：
```json
{
    "timestamp": "2026-06-02T10:00:00Z",
    "level": "INFO",
    "module": "chat",
    "message": "User sent message",
    "user_id": 123,
    "conversation_id": 456
}
```

---

## 九、性能优化

### 9.1 数据库优化

1. **索引优化**：为常用查询字段建立索引
2. **查询优化**：避免N+1查询，使用JOIN或预加载
3. **连接池**：配置合适的连接池大小
4. **分页查询**：使用游标分页，避免深度分页

### 9.2 缓存优化

1. **热点数据缓存**：用户信息、配置数据
2. **查询结果缓存**：复杂查询结果缓存
3. **缓存预热**：系统启动时预加载热点数据
4. **缓存更新**：合理的缓存失效策略

### 9.3 异步优化

1. **异步IO**：所有IO操作使用异步
2. **并发控制**：限制并发请求数
3. **超时设置**：合理的超时时间
4. **重试机制**：失败请求自动重试

---

*创建日期：2026-06-02*
*基于医小管v2项目代码和文档整理*
