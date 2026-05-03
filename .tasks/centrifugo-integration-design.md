# Centrifugo 集成架构设计

> 版本: v1.0
> 日期: 2026-05-04
> 状态: 待确认后执行

---

## 一、动机与问题分析

### 1.1 当前架构的致命缺陷

```
客户端 ──WS──→ FastAPI (单 worker) ──→ 内存 dict (ws_manager.py)
```

| 问题 | 根因 | 影响 |
|------|------|------|
| 多 worker 不共享 | `ConnectionManager` 是进程级全局变量 | uvicorn `--workers 2` 时，worker A 的连接收不到 worker B 广播的消息 |
| 无消息持久化保证 | `ws.py` 的 `send_message` 只广播不入库 | 网络闪断 = 消息丢失 |
| 断线无恢复 | 重连后只能 rejoinRoom，丢失断线期间消息 | 用户体验"一步一卡" |
| 心跳自行维护 | 30s 间隔 ping/pong 由前端管理 | 代码冗余，不同端实现有差异 |
| 无在线状态 | 后端不知道谁在线 | 教师无法看到学生是否在线 |
| 不支持水平扩展 | 内存 dict 无法跨进程/跨机器 | 永远只能单 worker |

### 1.2 Centrifugo 如何解决

| 问题 | Centrifugo 方案 |
|------|----------------|
| 多 worker 共享 | 后端通过 HTTP API 发布消息到 Centrifugo，与 worker 数量无关 |
| 消息持久化 | 后端先写 DB 再 publish，publish 只是"通知"，不承担持久化 |
| 断线恢复 | Centrifugo 内置 history + recover（可配置保留 N 条或 N 秒） |
| 心跳 | SDK 自动管理，前端零代码 |
| 在线状态 | Centrifugo 内置 presence API |
| 水平扩展 | Centrifugo 单实例支持 100k+ 连接，可用 Redis 做多节点共享 |

---

## 二、目标架构

```
                          ┌─────────────────────────────┐
                          │        Centrifugo            │
                          │  (Go, Docker, :8000)         │
                          │                             │
                          │  ┌──────────────────────┐   │
                          │  │ 频道:                 │   │
                          │  │  conv:{id}           │   │  ← 会话消息
                          │  │  user#{id}           │   │  ← 个人通知 (server-side sub)
                          │  │  $teachers           │   │  ← 教师全局 (server-side sub)
                          │  └──────────────────────┘   │
                          │                             │
                          │  JWT 认证 (共享 secret)       │
                          │  History: 100 条 / 5 分钟     │
                          │  Presence: 开启              │
                          └──────┬────────────┬─────────┘
                                 │            │
                      WebSocket  │            │  HTTP API (publish)
                                 │            │
                    ┌────────────┘            └────────────┐
                    │                                      │
        ┌───────────┴───────────┐          ┌───────────────┴────────────┐
        │   客户端               │          │   FastAPI Gateway          │
        │                       │          │                            │
        │  学生 H5 (centrifuge-js) │       │  POST /api/chat/send       │
        │  教师 H5 (centrifuge-js) │       │    → 写 DB                 │
        │                       │          │    → publish conv:{id}     │
        │  订阅:                │          │                            │
        │    conv:{id}          │          │  POST /api/conversations/  │
        │    (自动 recover)      │          │    {id}/messages           │
        │                       │          │    → 写 DB                 │
        │  接收:                │          │    → publish conv:{id}     │
        │    new_message        │          │                            │
        │    status_changed     │          │  POST /api/actions/escalate│
        │    typing             │          │    → 状态变更              │
        │    escalation_notify  │          │    → publish conv:{id}     │
        │                       │          │    → publish user#{tid}    │
        └───────────────────────┘          └────────────────────────────┘
```

---

## 三、详细设计

### 3.1 频道命名规范

| 频道 | 用途 | 订阅者 | 订阅方式 |
|------|------|--------|----------|
| `conv:{conv_id}` | 会话内的消息和状态变更 | 会话中的学生 + 教师 | **客户端主动订阅** (进入会话详情页时) |
| `user#{user_id}` | 个人通知：新工单分配、系统消息 | 当前用户 | **服务端订阅** (连接时自动) |
| `$teachers` | 教师全局广播：新待接工单提醒 | 所有在线教师 | **服务端订阅** (教师连接时自动) |

> 命名约定：`#` 前缀 = 服务端订阅频道 (server-side subscription)，`$` 前缀 = 受保护频道 (需要 JWT claims 中声明权限)

### 3.2 Centrifugo 配置

```json
{
  "token_hmac_secret_key": "${YXG_JWT_SECRET}",
  "admin": false,
  "api_key": "${CENTRIFUGO_API_KEY}",
  "allowed_origins": [
    "https://yxg.xiaoguan.site",
    "https://teacher.xiaoguan.site"
  ],
  "namespaces": [
    {
      "name": "conv",
      "history_size": 100,
      "history_ttl": "5m",
      "force_recovery": true,
      "presence": true,
      "join_leave": false
    },
    {
      "name": "user",
      "server_side": true
    }
  ],
  "channel_options": {
    "$teachers": {
      "server_side": true,
      "presence": true
    }
  },
  "proxy_connect_endpoint": "",
  "proxy_subscribe_endpoint": ""
}
```

### 3.3 JWT Token 设计

```python
# 后端: 新增 /api/auth/centrifugo-token 端点
# 也可在 login 响应中一并返回

def build_centrifugo_token(user: User) -> str:
    """生成 Centrifugo 连接 JWT"""
    now = int(time.time())
    payload = {
        "sub": str(user.id),           # 用户 ID (Centrifugo 要求 string)
        "exp": now + 3600,             # 1 小时过期
        "info": {                      # 附加信息，其他订阅者可见
            "name": user.name,
            "role": user.role.value,
        },
        "channels": _build_server_channels(user),  # 服务端自动订阅的频道
    }
    return jwt.encode(payload, CENTRIFUGO_SECRET, algorithm="HS256")


def _build_server_channels(user: User) -> list[str]:
    """根据角色决定服务端自动订阅的频道"""
    channels = [f"user#{user.id}"]     # 每个用户都订阅自己的通知频道
    if user.role in (UserRole.teacher, UserRole.admin):
        channels.append("$teachers")   # 教师/管理员订阅教师全局频道
    return channels
```

**决策：在 login 响应中一并返回 `centrifugo_token`**

理由：
- 减少一次网络往返
- 登录后客户端立即建立 Centrifugo 连接，无延迟
- token 过期后通过 SDK 的 `getToken` 回调自动刷新

```python
# 修改 LoginResponse
class TokenResponse(BaseModel):
    access_token: str
    centrifugo_token: str  # 新增
```

### 3.4 消息流详解

#### 场景 1：学生发消息（AI 回复）

```
1. 学生前端 POST /api/chat/send {content: "怎么选课"}
2. 后端:
   a. 写 student_msg 到 DB
   b. publish("conv:{conv_id}", {type: "new_message", data: student_msg})
   c. 调 Dify SSE 获取 AI 回复
   d. 写 ai_msg 到 DB
   e. publish("conv:{conv_id}", {type: "new_message", data: ai_msg})
3. 学生前端收到两条 publication（自己的消息回显 + AI 回复）
4. 如果教师也订阅了这个 conv，同步看到
```

#### 场景 2：教师发消息

```
1. 教师前端 POST /api/conversations/{id}/messages {content: "..."}
2. 后端:
   a. 写 msg 到 DB
   b. publish("conv:{conv_id}", {type: "new_message", data: msg})
3. 学生前端实时收到
4. 教师前端也收到（回显确认，或可用乐观更新 + 去重）
```

#### 场景 3：学生转人工

```
1. 学生前端 POST /api/actions/{id}/escalate
2. 后端:
   a. transition(conv, "escalate") → pending_teacher
   b. publish("conv:{conv_id}", {type: "status_changed", data: {status: "pending_teacher"}})
   c. 查本学院教师列表 → 对每个 teacher_id:
      publish("user#{teacher_id}", {type: "escalation_notify", data: {conv_id, student_name, ...}})
   d. publish("$teachers", {type: "new_pending", data: {conv_id, college, ...}})
3. 学生看到"等待老师接入..."
4. 学院教师收到个人通知 + 全局教师频道通知
```

#### 场景 4：教师接单

```
1. 教师前端 POST /api/actions/{id}/accept
2. 后端:
   a. transition(conv, "accept") → teacher_serving
   b. publish("conv:{conv_id}", {type: "status_changed", data: {status: "teacher_serving", teacher_name}})
   c. publish("$teachers", {type: "ticket_accepted", data: {conv_id}})  # 通知其他教师该工单已被接
3. 学生看到"老师已接入"
4. 其他教师的工单列表中该工单状态更新
```

#### 场景 5：打字提示（typing）

```
1. 教师打字时，前端直接通过 Centrifugo client publish:
   centrifuge.publish("conv:{conv_id}", {type: "typing", user_id, role: "teacher"})
2. 学生端收到 → 显示"老师正在输入..."
3. 不经过后端，零延迟

注意: Centrifugo 支持客户端直接 publish（需在 namespace 配置 "allow_publish_for_client": true）
但 typing 这种临时性消息适合客户端直发，不走后端
```

### 3.5 前端 SDK 封装

```typescript
// utils/centrifuge.ts — 替代 websocket.ts
import { Centrifuge, Subscription } from 'centrifuge'

type EventHandler = (data: any) => void

class CentrifugeManager {
  private client: Centrifuge | null = null
  private subscriptions: Map<string, Subscription> = new Map()
  private handlers: Map<string, Set<EventHandler>> = new Map()

  /**
   * 初始化连接。登录后调用。
   * @param centrifugoToken 从 login API 返回的 centrifugo_token
   * @param getToken 刷新 token 的回调（可选，用于 token 过期续期）
   */
  connect(centrifugoToken: string, getToken?: () => Promise<string>) {
    const wsUrl = location.protocol === 'https:'
      ? `wss://${location.host}/centrifugo/connection/websocket`
      : `ws://${location.host}/centrifugo/connection/websocket`

    this.client = new Centrifuge(wsUrl, {
      token: centrifugoToken,
      getToken: getToken,   // SDK 自动在 token 过期前调用
    })

    // 服务端订阅的频道（user#{id}, $teachers）在这里自动接收
    this.client.on('publication', (ctx) => {
      // 服务端订阅频道的消息通过顶层事件分发
      this.dispatch(ctx.data?.type || 'unknown', ctx.data?.data || ctx.data)
    })

    this.client.on('connected', () => {
      console.log('[Centrifuge] connected')
      this.dispatch('_connected', {})
    })

    this.client.on('disconnected', (ctx) => {
      console.log('[Centrifuge] disconnected', ctx.reason)
      this.dispatch('_disconnected', { reason: ctx.reason })
    })

    this.client.connect()
  }

  disconnect() {
    this.subscriptions.forEach(sub => sub.unsubscribe())
    this.subscriptions.clear()
    this.client?.disconnect()
    this.client = null
  }

  /**
   * 订阅会话频道。进入会话详情页时调用。
   * 内置断线恢复：重连后自动补发断线期间的消息。
   */
  joinConversation(convId: number) {
    const channel = `conv:${convId}`
    if (this.subscriptions.has(channel)) return

    const sub = this.client!.newSubscription(channel, {
      recoverable: true,  // 启用断线恢复
    })

    sub.on('publication', (ctx) => {
      const msg = ctx.data
      this.dispatch(msg?.type || 'unknown', msg?.data || msg)
    })

    sub.on('recover', (ctx) => {
      console.log(`[Centrifuge] recovered ${ctx.publications?.length || 0} messages for conv:${convId}`)
    })

    sub.subscribe()
    this.subscriptions.set(channel, sub)
  }

  /**
   * 离开会话频道。退出会话详情页时调用。
   */
  leaveConversation(convId: number) {
    const channel = `conv:${convId}`
    const sub = this.subscriptions.get(channel)
    if (sub) {
      sub.unsubscribe()
      this.subscriptions.delete(channel)
    }
  }

  /**
   * 发送 typing 提示（客户端直发，不经后端）
   */
  sendTyping(convId: number, userId: number, role: string) {
    const channel = `conv:${convId}`
    const sub = this.subscriptions.get(channel)
    sub?.publish({ type: 'typing', user_id: userId, role })
  }

  // 事件系统：与旧 wsManager 保持相同 API
  on(type: string, handler: EventHandler) {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(handler)
  }

  off(type: string, handler: EventHandler) {
    this.handlers.get(type)?.delete(handler)
  }

  private dispatch(type: string, data: any) {
    this.handlers.get(type)?.forEach(h => {
      try { h(data) } catch (e) { console.error('[Centrifuge dispatch]', e) }
    })
  }
}

export const centrifugeManager = new CentrifugeManager()
```

**关键设计：事件 API 与旧 `wsManager` 保持一致** (`on/off/joinRoom/leaveRoom`)，
前端页面代码改动最小——只需替换 import 路径。

### 3.6 后端 Centrifugo HTTP 客户端

```python
# services/centrifugo_client.py
import httpx
import logging

logger = logging.getLogger(__name__)

class CentrifugoClient:
    """Centrifugo Server API 客户端"""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key

    async def publish(self, channel: str, data: dict) -> bool:
        """向指定频道发布消息"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api/publish",
                    json={"channel": channel, "data": data},
                    headers={"Authorization": f"apikey {self.api_key}"},
                    timeout=5.0,
                )
                if resp.status_code != 200:
                    logger.error(f"Centrifugo publish failed: {resp.status_code} {resp.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Centrifugo publish error: {e}")
            return False

    async def broadcast(self, channels: list[str], data: dict) -> bool:
        """向多个频道广播同一消息"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api/broadcast",
                    json={"channels": channels, "data": data},
                    headers={"Authorization": f"apikey {self.api_key}"},
                    timeout=5.0,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Centrifugo broadcast error: {e}")
            return False

# 全局单例（从环境变量初始化）
centrifugo = CentrifugoClient(
    api_url=os.getenv("CENTRIFUGO_API_URL", "http://127.0.0.1:8000"),
    api_key=os.getenv("CENTRIFUGO_API_KEY", ""),
)
```

### 3.7 后端改造点清单

| 文件 | 当前代码 | 改为 |
|------|---------|------|
| `routers/auth.py` | 返回 `access_token` | 同时返回 `centrifugo_token` |
| `routers/conversations.py` | `manager.broadcast_to_room(...)` (4处) | `centrifugo.publish("conv:{id}", ...)` |
| `routers/chat.py` | `manager.broadcast_to_room(...)` (3处) | `centrifugo.publish("conv:{id}", ...)` |
| `routers/actions.py` | `manager.broadcast_to_room(...)` (4处) + `broadcast_to_college_teachers(...)` (1处) | `centrifugo.publish("conv:{id}", ...)` + `centrifugo.broadcast(["user#{tid}" for tid in teacher_ids], ...)` |
| `routers/ws.py` | WebSocket 端点 (整个文件) | **标记 @deprecated**，保留 2 周兼容期后删除 |
| `services/ws_manager.py` | ConnectionManager 全局单例 | 同上，保留 → 删除 |

**总改动**: 后端约 12 处 `manager.xxx` 调用替换为 `centrifugo.publish`，+ 新增 2 个文件。

---

## 四、部署方案

### 4.1 Docker Compose

```yaml
# deploy/docker-compose.centrifugo.yml
services:
  centrifugo:
    image: centrifugal/centrifugo:v6
    container_name: yxg-centrifugo
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"    # 只监听 localhost，nginx 反代
    volumes:
      - ./centrifugo-config.json:/centrifugo/config.json:ro
    command: centrifugo -c config.json
    environment:
      - CENTRIFUGO_TOKEN_HMAC_SECRET_KEY=${YXG_JWT_SECRET}
      - CENTRIFUGO_API_KEY=${CENTRIFUGO_API_KEY}
```

### 4.2 nginx 反代

```nginx
# 在 yxg-student-domain 和 yxg-teacher-domain 两个 vhost 中都加

location /centrifugo/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

### 4.3 环境变量 (.env 新增)

```bash
# Centrifugo
CENTRIFUGO_API_URL=http://127.0.0.1:8000
CENTRIFUGO_API_KEY=<生成一个随机 key>
CENTRIFUGO_SECRET=${JWT_SECRET}       # 复用现有 JWT secret
```

---

## 五、迁移策略

### 5.1 分阶段上线

```
Phase 1: 部署 Centrifugo (Day 1)
  ├── HK 服务器部署 Centrifugo Docker 容器
  ├── nginx 配置反代
  ├── 验证 Centrifugo 健康检查 /health
  └── 手动测试: curl publish 到频道

Phase 2: 后端双写 (Day 1-2)
  ├── 新增 centrifugo_client.py
  ├── 所有 broadcast 调用改为 centrifugo.publish
  ├── 同时保留旧 ws_manager 广播（双写）
  ├── login 返回 centrifugo_token
  └── 部署后端

Phase 3: 前端切换 (Day 2-3)
  ├── 新增 centrifuge.ts（保持旧 API 兼容）
  ├── 教师端 detail.vue 切换到 centrifugeManager
  ├── 学生端 chat/index.vue 切换到 centrifugeManager
  ├── stores/websocket.ts 更新
  └── 部署前端

Phase 4: 清理 (Day 3-5)
  ├── 确认线上无人使用旧 WS
  ├── 移除后端双写（删除 ws_manager 调用）
  ├── 标记 ws.py 和 ws_manager.py 为 deprecated
  ├── 2 周后彻底删除
  └── 更新测试代码中的 mock
```

### 5.2 回滚方案

如果 Centrifugo 出问题：
1. 前端回退到旧 `websocket.ts`（git revert 前端 commit）
2. 后端已有双写，旧 WS 路径仍然可用
3. nginx 移除 `/centrifugo/` location 即可

### 5.3 兼容期设计

前端可以做智能降级：

```typescript
// 如果 Centrifugo 连接失败，自动降级到旧 WS
centrifugeManager.on('_disconnected', ({ reason }) => {
  if (reason === 'transport_closed' && !centrifugoAvailable) {
    console.warn('[Centrifuge] fallback to legacy WS')
    wsManager.connect(token)
  }
})
```

---

## 六、前端改造对照表

### 6.1 教师端 (teacher-app)

| 文件 | 改动 |
|------|------|
| `utils/websocket.ts` → `utils/centrifuge.ts` | 新增 SDK 封装 |
| `stores/websocket.ts` | `wsManager.connect(token)` → `centrifugeManager.connect(centrifugoToken)` |
| `pages/questions/detail.vue` | `wsManager.joinRoom(id)` → `centrifugeManager.joinConversation(id)` |
| | `wsManager.on('new_message', ...)` → `centrifugeManager.on('new_message', ...)` |
| | `wsManager.leaveRoom(id)` → `centrifugeManager.leaveConversation(id)` |
| `api/auth.ts` | 解析 login 响应中的 `centrifugo_token` 并存储 |

### 6.2 学生端 (student-app)

| 文件 | 改动 |
|------|------|
| `utils/websocket.ts` → `utils/centrifuge.ts` | 同教师端，完全复用 |
| `pages/chat/index.vue` | `wsManager.send({type:'join_room',...})` → `centrifugeManager.joinConversation(id)` |
| | `wsManager.on('new_message', ...)` → 保持不变（API 兼容）|
| `api/auth.ts` | 同教师端 |

### 6.3 事件名映射（完全兼容，无需改）

| 旧事件 | Centrifugo 事件 | 来源 |
|--------|----------------|------|
| `new_message` | `new_message` | conv:{id} 频道 publication |
| `status_changed` | `status_changed` | conv:{id} 频道 publication |
| `escalation_notify` | `escalation_notify` | user#{id} 服务端订阅 |
| `teacher_typing` / `student_typing` | `typing` | conv:{id} 客户端 publish |
| `_connected` / `_disconnected` | 同名 | SDK 事件 |

---

## 七、测试计划

### 7.1 单元测试

```python
# 后端: mock centrifugo.publish
@pytest.mark.asyncio
async def test_send_message_publishes_to_centrifugo(monkeypatch):
    publish_mock = AsyncMock(return_value=True)
    monkeypatch.setattr("app.routers.conversations.centrifugo.publish", publish_mock)
    # ... 调用 send_message ...
    publish_mock.assert_called_once_with(
        "conv:123",
        {"type": "new_message", "data": {...}}
    )
```

### 7.2 集成测试

```bash
# 1. 启动 Centrifugo
docker compose -f deploy/docker-compose.centrifugo.yml up -d

# 2. 验证连接
curl http://127.0.0.1:8000/health  # 应返回 {"status": "ok"}

# 3. 手动 publish 测试
curl -X POST http://127.0.0.1:8000/api/publish \
  -H "Authorization: apikey ${CENTRIFUGO_API_KEY}" \
  -d '{"channel": "conv:1", "data": {"type": "test", "content": "hello"}}'

# 4. E2E: 两个浏览器标签页，一个学生一个教师
#    学生发消息 → 教师实时收到
#    教师回复 → 学生实时收到
```

### 7.3 断线恢复测试

```
1. 学生订阅 conv:1
2. 断开学生网络
3. 教师发 3 条消息
4. 恢复学生网络
5. 验证学生自动收到 3 条消息（Centrifugo recover）
```

---

## 八、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Centrifugo 崩溃 | 低 | 实时推送断，但消息仍在 DB | Docker restart policy + 前端降级到旧 WS |
| HK 服务器资源不足 | 中 | Centrifugo 占用额外内存 | Centrifugo 空载约 20MB，100 连接约 50MB，完全够 |
| JWT secret 不一致 | 低 | 认证失败 | 复用同一个 secret，.env 配置 |
| 前端 SDK 兼容性 | 低 | uni-app H5 模式下 centrifuge-js 不工作 | centrifuge-js 纯 JS，不依赖 Node API，H5 兼容 |
| 网络层面 nginx WebSocket 超时 | 中 | 长连接被断 | `proxy_read_timeout 3600s` |

---

## 九、工作量总结

| 阶段 | 工作项 | 预估工时 | 可并行 |
|------|--------|----------|--------|
| Phase 1 | Centrifugo 部署 + nginx | 2h | — |
| Phase 2 | centrifugo_client.py + 后端改造 (12 处替换) | 4h | 可与 Phase 1 并行 |
| Phase 2 | centrifugo_token 端点 + login 改造 | 1h | — |
| Phase 3 | centrifuge.ts SDK 封装 | 2h | — |
| Phase 3 | 教师端页面切换 | 2h | — |
| Phase 3 | 学生端页面切换 | 2h | 可与教师端并行 |
| Phase 4 | 测试 + 清理 | 3h | — |
| **合计** | — | **~16h (2-3 天)** | — |

---

## 十、依赖与前置条件

1. ✅ HK 服务器有 Docker (已确认)
2. ✅ nginx 支持 WebSocket 反代 (已确认)
3. ⬜ 需要生成 `CENTRIFUGO_API_KEY` (随机字符串)
4. ⬜ 需要确认 `JWT_SECRET` 在 gateway .env 中的变量名
5. ⬜ 需要 `npm install centrifuge` (teacher-app + student-app)

---

*本文档包含完整的架构设计、改造清单、部署方案和迁移策略，可直接作为实施指南。*
