# 教师端功能评估报告 — 工单处理 & 知识入库

> 评估时间: 2026-05-04
> 评估人: Cascade (基于代码审查 + 网络调研)

---

## 一、功能完整度矩阵

### 后端 Gateway (services/gateway/)

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 会话 CRUD | `routers/conversations.py` | ✅ 完整 | 创建/列表/详情/发消息/未读/标已读 |
| 状态机 | `services/state_machine.py` | ✅ 完整 | 6种状态 + 7种转换 + 系统消息自动写入 |
| 教师接单 | `routers/conversations.py` (accept) | ✅ 完整 | 通过 state_machine transition |
| 教师发消息 | `routers/conversations.py:116-178` | ✅ 完整 | HTTP POST + WS 广播双通道 |
| WebSocket Hub | `routers/ws.py` + `services/ws_manager.py` | ⚠️ 基础可用 | 见下方详细分析 |
| 知识-高频问题 | `routers/knowledge.py` (unanswered-top) | ✅ 完整 | |
| 知识-草稿提交 | `routers/knowledge.py` (drafts) | ✅ 完整 | AI 润色 + scope 分级 |
| 知识-审核流程 | `routers/knowledge.py` (reviews) | ✅ 完整 | approve / reject + 双路径兼容 |
| Dify AI 对话 | `routers/chat.py` | ✅ 完整 | SSE 流式 + 知识库检索 |

### 教师端前端 (apps/teacher-app/)

| 页面 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 工单列表 | `questions/index.vue` | ✅ 完整 | 筛选/搜索/分页 |
| 工单详情 | `questions/detail.vue` | ✅ 完整 | 接单/回复/解决 + WS 实时推送 |
| 知识库列表 | `knowledge/index.vue` | ✅ 完整 | 教师视角(高频待补+我的知识) + 管理员视角(待审核) |
| 知识详情 | `knowledge/detail.vue` | ✅ 完整 | 查看/编辑 |
| WebSocket 客户端 | `utils/websocket.ts` | ✅ 完整 | 重连/心跳/房间/队列 |
| Dashboard | `dashboard/index.vue` | ⚠️ 占位符 | 有 UI 但数据可能是静态 |

---

## 二、工单处理（实时对话）深度评估

### 2.1 当前架构

```
学生 H5 ──→ FastAPI WebSocket ←── 教师 H5
             ↕ (内存 dict)
          ws_manager.py
          ConnectionManager
```

**核心问题：这是一个「纯内存单进程」WebSocket 实现。**

### 2.2 具体痛点

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| **单进程瓶颈** | 🔴 致命 | `ws_manager.py` 用 Python dict 管连接，多 worker 时连接不共享 |
| **WS send_message 不写库** | 🟡 中等 | `ws.py:88-106` 注释说"仅广播不写库"，正式消息靠 HTTP API，但前端可能混用 |
| **无消息持久化保证** | 🟡 中等 | WS 断线期间的消息会丢失，重连后靠 HTTP 拉取 |
| **无消息 ACK** | 🟡 中等 | 发出即忘，不知道对方是否收到 |
| **教师需手动刷新** | 🟡 中等 | `detail.vue:93` 有"点击刷新"按钮作为 WS 不可靠时的兜底 |
| **心跳 30s** | 🟢 小问题 | 合理但某些 nginx/LB 可能 60s 超时 |
| **无在线状态** | 🟢 小问题 | 不知道对方是否在线 |

### 2.3 你说的"一步一卡"的根本原因

1. **消息发送走 HTTP → WS 广播是两步**，延迟叠加
2. **uni-app 的 `uni.connectSocket` 在某些平台有兼容性问题**
3. **没有乐观更新（optimistic update）**：发消息后等 HTTP 返回才显示
4. **WS 重连期间消息可能丢失**，只能靠手动刷新补偿
5. **nginx 代理 WebSocket 配置复杂**，容易出现连接中断

---

## 三、知识入库功能评估

### 3.1 流程完整度

```
学生提问 → AI 无法回答 → 记录到 unanswered_questions 表
                              ↓
教师看到「高频待补」列表 → 输入口语化答复 → AI 润色
                              ↓
              ┌─ scope=class/college → 直接发布 ✅
              └─ scope=global → 提交管理员审核 → approve/reject
```

**结论：知识入库后端 + 前端流程完整，是目前最成熟的模块。**

### 3.2 问题

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| 前端空白 | 🟡 待验证 | 你说"知识入库界面是空的"——可能是数据库无数据，或 API 调不通 |
| AI 润色无前端展示 | 🟢 小问题 | 提交后直接发布，没有让教师预览润色结果 |
| 无批量操作 | 🟢 小问题 | 管理员审核只能逐条操作 |

---

## 四、参考项目 ByteDesk

你在 V1 时期找到的就是 **ByteDesk**（微语）。本地已有参考副本 `C:\Users\Administrator\Documents\code\bytedesk-ref\`。

### 4.1 ByteDesk 概况

| 维度 | 详情 |
|------|------|
| **GitHub** | https://github.com/Bytedesk/bytedesk (⭐5k+) |
| **技术栈** | Spring Boot + MySQL/PostgreSQL + Artemis MQ + Redis |
| **前端** | React/Flutter/UniApp SDK |
| **核心模块** | TeamIM / Customer Service / Knowledge Base / Ticket / AI Agent / Workflow |
| **协议** | BSL 1.1（商用需授权） |
| **部署** | Docker Compose 一键启动 |

### 4.2 ByteDesk vs 医小管 v2

| 能力 | ByteDesk | 医小管 v2 |
|------|----------|-----------|
| 实时聊天 | ✅ 成熟 MQ + WS | ⚠️ 单进程内存 dict |
| 工单系统 | ✅ 完整 SLA + 统计 | ✅ 基础状态机 |
| 知识库 | ✅ HelpCenter + FAQ + RAG | ✅ 教师入库 + AI 润色 |
| AI Agent | ✅ Ollama/DeepSeek/RAG | ✅ Dify 集成 |
| 组织架构 | ✅ 多层级 | ⚠️ 学院/班级二级 |
| 审核流程 | ✅ Workflow 引擎 | ✅ 简单 approve/reject |
| **问题** | 🔴 Java 生态，过于庞大，BSL 商用限制 | 🟢 Python 轻量，完全自主 |

### 4.3 为什么当时没用 ByteDesk

> 项目过于庞大，Java + Spring Boot 全家桶，嵌入成本极高，且 BSL 许可证限制商用。

---

## 五、成熟替代方案评估

### 5.1 实时通信层（替代手写 WebSocket）

| 方案 | 类型 | 语言 | 适配成本 | 推荐度 |
|------|------|------|----------|--------|
| **Centrifugo** | 独立 WS 服务器 | Go | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ **强烈推荐** |
| **Socket.IO** | 库 | JS/Python | ⭐ 低 | ⭐⭐⭐ 可用 |
| **腾讯云 IM (TIM)** | 云服务 | 多语言 SDK | ⭐ 低 | ⭐⭐⭐⭐ 但付费 |
| **网易云信 NIM** | 云服务 | 多语言 SDK | ⭐ 低 | ⭐⭐⭐⭐ 但付费 |

#### **推荐方案：Centrifugo**

理由：
1. **Go 编写，单二进制**，Docker 一行启动
2. **原生支持 Redis/NATS** 做多节点横向扩展
3. **消息历史恢复**（recovery）：断线重连自动补发丢失消息
4. **在线状态 (presence)**：内置
5. **频道/房间**：与现有 `conv:{id}` 模型完美对应
6. **FastAPI 集成简单**：只需用 HTTP API 发布消息到 Centrifugo，客户端直连 Centrifugo
7. **支持 JWT 认证**：与现有 auth 系统兼容
8. 100万并发连接 / 3000万消息/分钟（官方基准测试）

```
改造前:
  学生 ──WS──→ FastAPI (单进程内存) ←──WS── 教师

改造后:
  学生 ──WS──→ Centrifugo ←──WS── 教师
                  ↕ (HTTP API)
               FastAPI (业务逻辑 + 写库)
```

### 5.2 整体客服方案（如果不想自己维护）

| 方案 | 开源 | 技术栈 | 特点 | 适配难度 |
|------|------|--------|------|----------|
| **Chatwoot** | ✅ MIT | Ruby on Rails + Vue | 最成熟的开源客服平台，自托管 | ⭐⭐⭐ 高(重新部署) |
| **微语/ByteDesk** | ⚠️ BSL | Spring Boot + React | 中文友好，功能全 | ⭐⭐⭐⭐ 很高(Java) |
| **Helpy** | ✅ MIT | Ruby on Rails | 工单 + 知识库 + 社区 | ⭐⭐⭐ 高 |
| **Frappe Helpdesk** | ✅ MIT | Python (Frappe) | 工单 + 知识库，轻量 | ⭐⭐ 中等 |
| **NocoBase** | ✅ AGPL | TypeScript | 低代码平台，可搭工单系统 | ⭐⭐ 中等 |

### 5.3 聊天 UI 组件（加速前端开发）

| 组件 | 平台 | 说明 |
|------|------|------|
| **腾讯 chat-uikit-uniapp** | uni-app (Vue 2/3) | 完整聊天 UI，但绑定腾讯云 IM |
| **网易云信 nim-uikit-uniapp** | uni-app | 类似，绑定网易云信 |
| **vue-advanced-chat** | Vue 3 | 纯前端聊天组件，可配任意后端 |

---

## 六、🔴 致命问题：账号角色未隔离

### 现状

学生端和教师端都调用同一个 `/api/auth/login` 端点，后端 `auth_service.py:8-17` 只校验 `staff_id + password`，**完全不检查角色**：

```python
# auth_service.py — 当前代码
async def authenticate_user(db, staff_id, password):
    stmt = select(User).where(User.staff_id == staff_id, User.is_active == True)
    # ← 没有 role 过滤
```

**后果**：
- Admin 可以登录学生端 → 看到学生界面，行为不可预期
- 教师可以登录学生端 → 可能触发学生才能做的操作
- 学生可以登录教师端 → 权限不足时才报 403，但已经能看到界面

### 修复方案

**方案 1（推荐）：后端加 `expected_role` 参数**

```python
# 修改 LoginRequest schema 加 expected_role 字段（可选）
# 学生端传 expected_role="student"
# 教师端传 expected_role="teacher" 或 "admin"
# 后端校验不匹配时返回 403
```

**方案 2：前端 `getMe()` 后校验角色**

```typescript
// 登录成功后立刻检查 role
const me = await getMe()
if (me.role !== 'student') {
  // 清除 token，跳转到错误提示
}
```

**建议**：两个方案都做。后端做主拦截，前端做二次校验 + 友好提示。

---

## 七、行动建议

### 方案 A：最小改造（推荐，1-2天）

> 保持现有架构，仅解决"一步一卡"的体验问题

1. **前端乐观更新**：发消息后立刻渲染到界面，不等 HTTP 返回
2. **WS 消息回显**：HTTP 发消息成功后，WS 广播包含完整 `msg.id`，前端去重
3. **断线恢复**：WS 重连后自动 HTTP 拉取最新消息
4. **nginx WS 优化**：确保 `proxy_read_timeout 86400s` + `proxy_send_timeout 86400s`

### 方案 B：引入 Centrifugo（推荐，3-5天）

> 把实时通信层换成 Centrifugo，从根本上解决可靠性和扩展性

1. Docker 部署 Centrifugo（1 行）
2. 后端改为 HTTP API → Centrifugo publish（替代 ws_manager.py）
3. 前端改为 centrifuge-js SDK 连接（替代 uni.connectSocket）
4. 保留现有 HTTP API 做消息持久化

### 方案 C：接入腾讯/网易 IM SDK（不推荐，除非要做微信小程序）

> 需要付费，且过度依赖第三方

### 方案 D：引入 Chatwoot/ByteDesk 整体替换（不推荐）

> 过于庞大，技术栈不匹配，等于重写

---

## 七、总结

| 模块 | 现状 | 结论 |
|------|------|------|
| **知识入库** | ✅ 功能完整，可能只是数据/部署问题 | 优先排查线上数据库和 API 连通性 |
| **工单状态机** | ✅ 设计合理 | 保持不动 |
| **实时对话** | ⚠️ 可用但体验差 | 短期做方案 A，中期做方案 B |
| **前端 UI** | ✅ 基本完整 | 远端机器做美化即可 |
