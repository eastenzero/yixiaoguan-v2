# 教师端功能现状审计报告

> **日期**: 2026-05-04  
> **项目**: 医小管 v2  
> **范围**: 教师端工单处理 + 知识入库模块完整度评估  
> **方法**: 纯代码阅读审计，未执行任何命令，未修改任何文件

---

## 一、功能完整度矩阵

### 1.1 后端 Gateway 端点

| 端点 | 方法 | 状态 | 备注 |
|------|------|------|------|
| `/api/auth/login` | POST | ✅ 完整 | 登录认证 |
| `/api/auth/me` | GET | ✅ 完整 | 当前用户信息 |
| `/api/chat/send` | POST | ✅ 完整 | 学生发消息，SSE 流式 AI + JSON 教师路径 |
| `/api/conversations` | POST | ✅ 完整 | 学生创建会话 |
| `/api/conversations` | GET | ✅ 完整 | 列表（教师按学院/状态过滤） |
| `/api/conversations/unread-summary` | GET | ✅ 完整 | 学生端未读汇总 |
| `/api/conversations/{id}/mark-read` | POST | ✅ 完整 | 标记已读 |
| `/api/conversations/{id}` | GET | ✅ 完整 | 会话详情（含权限校验） |
| `/api/conversations/{id}/messages` | GET | ✅ 完整 | 消息列表（分页） |
| `/api/conversations/{id}/messages` | POST | ✅ 完整 | 发送消息（学生/教师均可） |
| `/api/conversations/{id}/escalate` | POST | ✅ 完整 | 学生呼叫教师 → pending_teacher |
| `/api/conversations/{id}/accept` | POST | ✅ 完整 | 教师接单 → teacher_serving |
| `/api/conversations/{id}/resolve` | POST | ✅ 完整 | 教师解决 → resolved |
| `/api/conversations/{id}/close` | POST | ✅ 完整 | 关闭会话 → closed |
| `/ws` | WS | ✅ 完整 | JWT 认证，支持 join/leave room、typing、send_message、ping |
| `/api/v1/knowledge/unanswered-top` | GET | ✅ 完整 | 高频未答问题（教师/管理员） |
| `/api/v1/knowledge/drafts` | POST | ✅ 完整 | 教师提交知识草稿 → Dify 润色 → 发布/审核 |
| `/api/v1/knowledge/reviews/pending` | GET | ✅ 完整 | 管理员查看待审核列表 |
| `/api/v1/knowledge/reviews/{id}/approve` | POST | ✅ 完整 | 审核通过 → 发布到 Dify |
| `/api/v1/knowledge/reviews/{id}/reject` | POST | ✅ 完整 | 审核驳回 |
| `/api/admin/users` | GET | ✅ 完整 | 用户列表管理 |
| `/api/admin/users/batch-import` | POST | ✅ 完整 | 批量导入 |
| `/api/admin/users/{id}/reset-password` | POST | ✅ 完整 | 重置密码 |
| `/api/admin/users/{id}/toggle-active` | POST | ✅ 完整 | 启用/禁用 |
| `/api/v1/announcements` | POST/GET/PATCH/DELETE | ✅ 完整 | 通知公告 CRUD |
| `/api/v1/knowledge/entries` | GET | ❌ **缺失** | 知识条目列表（前端调用，无后端） |
| `/api/v1/knowledge/entries/{id}` | GET | ❌ **缺失** | 知识条目详情 |
| `/api/v1/knowledge/entries/{id}/offline` | POST | ❌ **缺失** | 知识下线条目 |
| `/api/v1/knowledge/categories` | GET | ❌ **缺失** | 知识分类 |
| `/api/v1/dashboard/stats` | GET | ❌ **缺失** | 工作台统计 |
| `/api/v1/dashboard/overview` | GET | ❌ **缺失** | 工作台聚合数据 |

### 1.2 教师端前端页面

| 页面 | 状态 | 关键能力 | 缺口 |
|------|------|----------|------|
| `pages/dashboard/index.vue` | ⚠️ 部分 | 欢迎横幅、快捷操作、统计网格、待处理列表、管理员入口 | stats/knowledgeCount/todayApprovals 无后端数据源；数据报告/系统设置为占位符弹窗 |
| `pages/questions/index.vue` | ✅ 完整 | 4 Tab 过滤（全部/待处理/处理中/已解决）、WS 实时推送、30s 轮询兜底 | — |
| `pages/questions/detail.vue` | ✅ 完整 | 会话消息渲染（学生/AI/教师/系统）、接单/回复/回复并解决、WS 实时消息推送、状态变更监听 | — |
| `pages/knowledge/index.vue` | ⚠️ 部分 | 高频待补列表（教师视图）、知识条目列表、待审核列表（管理员视图）、草稿提交、审核通过/驳回 | 知识条目列表无后端端点，靠 local storage 缓存和 API catch 降级 |
| `pages/knowledge/detail.vue` | ⚠️ 部分 | 知识详情展示、下线条目 | 编辑功能开发中（占位符），下线 API 无后端端点 |

### 1.3 前端 API 封装

| API 模块 | 状态 | 说明 |
|----------|------|------|
| `conversations.ts` | ✅ 完整 | 全部对接 v2 `/api/conversations/*` + `/api/conversations/{id}/accept` + `/api/conversations/{id}/resolve` |
| `knowledge.ts` | ⚠️ 部分 | `unanswered-top`、`drafts`、`reviews/*` 正常；`entries`、`entries/{id}`、`categories` 靠本地缓存降级 |
| `dashboard.ts` | ❌ 断裂 | 两个端点 (`/api/v1/dashboard/*`) 均无后端实现 |
| `escalation.ts` | ❌ 遗留 | v1 端点 (`/api/v1/escalations/*`)，当前页面已弃用，改用 conversations.ts |

---

## 二、工单处理流程评估

### 2.1 状态机设计：✅ 完善

状态流转表定义在 `services/gateway/app/services/state_machine.py:21-32`：

```
ai_serving ──escalate──→ pending_teacher ──accept──→ teacher_serving ──resolve──→ resolved
     │                         │                        │                          │
     └──────close───────────────┴──────close─────────────┴────────close─────────────┘
                                                                      ↑
                                                            resolved ──reactivate──→ ai_serving
```

- 5 个会话状态卡片：`ai_serving → pending_teacher → teacher_serving → resolved → closed`
- 6 个合法转换动作：escalate、accept、resolve、reactivate、close、timeout
- **timeout 转换已定义但未使用**（无人调度器从 pending_teacher 自动回退到 ai_serving）
- 每次状态变更自动写入系统消息，并 WS 广播到房间

### 2.2 WebSocket 实时对话：✅ 良好

**后端** (`ws.py`):
- 单 `/ws` 端点，JWT 认证
- 支持 6 种上行消息类型：`ping`、`join_room`、`leave_room`、`typing`、`send_message`
- `send_message` 当前仅广播不写库（代码注释注明 S2 阶段设计）
- 正式消息通过 HTTP `POST /api/conversations/{id}/messages` 发送，WS 仅通知

**前端** (`websocket.ts`):
- 单连接 + room 模式，支持 H5/小程序
- 断线重连（指数退避，最多 10 次，最大间隔 30s）
- 30s 心跳 ping
- 重连后自动 re-join 之前加入的房间
- 发送队列：离线时排队，连上后 flush

**消息实时性评估**: ✅
- 教师发送消息 → HTTP write DB → WS broadcast to room → 学生端实时收到
- 学生发送消息 → HTTP write DB + Dify SSE → WS broadcast AI response
- 状态变更 → HTTP transition + WS broadcast to room → 所有端实时更新

### 2.3 教师-学生对话闭环：✅ 完整

```
学生提问 → AI 回答 → 学生呼叫教师 ──escalate──→ pending_teacher
  → 教师端 WS 收到 escalation_notify
  → 教师点击接单 ──accept──→ teacher_serving
  → 教师输入回复 → WS 广播 → 学生实时看到
  → 教师点击"回复并解决" ──resolve──→ resolved
  → 学生继续提问 ──reactivate──→ ai_serving (循环)
```

### 2.4 已知缺陷

1. **timeout 超时回退未实现**: pending_teacher 状态下如果所有教师离线，应自动回退到 AI 服务，但无人调度器执行。
2. **WS send_message 仅广播不写库**: 代码注释标注为 S2 最小实现，正式生产应通过 HTTP API 保证事务性。
3. **学生端未读计数器只针对学生**：`/api/conversations/unread-summary` 硬编码 `role != student → return empty`，教师无法获知未读。
4. **无消息回执/已读状态**: 消息只有 `created_at`，没有 `delivered_at`/`read_at`。

---

## 三、知识入库流程评估

### 3.1 流程架构: ✅ 设计良好

```
学生提问 → AI 拒答/转人工 → UnansweredQuestion 记录（按问题文本去重，统计 hit_count）
  → 教师端 "高频待补" Tab 展示（按命中次数排序）
  → 教师点击 "去补充" → 输入答复 → 选择发布范围
  ├── 班级/学院发布 → Dify polish_text 润色 → 直接发布到 Dify 对应数据集 → SuggestionStatus.approved
  └── 全校发布 → Dify polish_text 润色 → 草稿存入 KbSuggestion → SuggestionStatus.pending
       → 管理员 "待审核" Tab → approve → 发布到 Dify global dataset
                              → reject → 驳回并显示原因
```

### 3.2 数据库模型: ✅ 完整

三张核心表：
- `unanswered_questions`: 高频未答问题（按 question_hash 去重）
- `kb_suggestions`: 知识草稿/审核条目（status: pending/approved/rejected）
- `college_datasets`: 学院 → Dify 数据集 ID 映射

### 3.3 Dify 集成: ✅ 完整

- 教师提交草稿时调用 `dify_client.polish_text()` 润色
- 发布时调用 `dify_client.create_document()` 写入对应 Dify 数据集
- 支持三个层级的数据集：全局（settings 配置）、学院（college_datasets 表映射）、班级（同学院）
- polish 失败时有 fallback（简单格式拼接）

### 3.4 权限控制: ✅ 合理

- 教师只能看到自己学院的待补问题和知识条目
- 教师只能发布到自己的学院/班级
- `global scope` 的发布需要管理员审核
- 管理员可看到所有待审核条目

### 3.5 前端降级策略: ⚠️ 有设计但不完整

`knowledge.ts` 实现了三层降级：
1. 正常 API 调用 (GET /api/v1/knowledge/entries)
2. API 失败 → 本地 local storage 缓存
3. 缓存中手动过滤/分页

但后端 `/api/v1/knowledge/entries` 端点根本不存在，导致始终走降级路径。审核操作（approve/reject）也有 `.catch()` 本地 fallback（模拟成功）。

### 3.6 已知缺陷

1. **`entries` CRUD 端点缺失**: 知识条目无法从列表获取、无法查看详情、无法下线。前端完全依赖 local storage 缓存。
2. **`categories` 端点缺失**: 前端调用但后端无实现。
3. **编辑功能开发中**: `detail.vue` L116 硬编码 `uni.showToast({ title: '编辑功能开发中' })`。
4. **UnansweredQuestion 生成机制不明**: 学生提问在什么条件下写入 `unanswered_questions` 表？是在 AI 拒答时？还是在转人工时？这在 `refusal.py` 中有关键词检测，但没有看到具体的写入调用代码。
5. **审批仅限 global scope**: `list_pending_reviews` 只查 `scope == global`，班级/学院发布的知识无需管理员审批就直接发布——这是设计意图，但可能导致低质量知识被直接发布到学院/班级数据集。

---

## 四、V1 参考信息发现

### 4.1 ByteDesk (微语 Bytedesk) 源码分析

**位置**: `yixiaoguan/.tasks/bytedesk-source-analysis.md`

已做过深度对比分析，关键发现：
- 微语的会话状态机设计（7 状态 vs 我们的 5 状态）
- 消息协议借鉴（消息类型枚举、extra 字段、发送者信息嵌入）
- 路由策略简化（微语的 Strategy 模式 → 我们用 if-else）
- 转接子状态机设计（微语独立维度管理，我们简化为会话状态一部分）

**结论**: 团队已明确决定**不引入 Bytedesk 作为底层平台**，而是借鉴其设计模式自己实现。

### 4.2 WebSocket vs 平台迁移辩论

**位置**: `yixiaoguan/.tasks/debate-websocket-vs-refactor/`

历史辩论结论：
- **不迁移**到 Chatwoot（Ruby + Rails，不支持小程序）
- **不迁移**到 Tiledesk（MongoDB + Node.js + Angular，技术栈完全不兼容）
- 现有自制方案已跑通核心流程，只需补充 WebSocket 基础设施

### 4.3 其他考察过的方案

| 方案 | 被否决原因 |
|------|-----------|
| ByteDesk (微语) | Java 后端兼容但 UI 不匹配，需二次开发量大于自建 |
| Chatwoot | Ruby on Rails，不支持 UniApp 小程序 |
| Tiledesk | MongoDB + Angular，技术栈零交集 |
| Dify 客服模式 | 只做 AI 问答，不解决人工对话问题 |
| FastGPT | 同上 |

### 4.4 V1 工单流程规范

**位置**: `yixiaoguan/.tasks/escalation-flow-spec.md`

详细记录了 v1 的工单闭环流程（6 个 Phase + 4 个 BUG），v2 的会话状态机正是基于此演化而来。

---

## 五、关键问题清单（按优先级排列）

### P0 — 阻断功能使用

| # | 问题 | 影响 | 修复文件 |
|---|------|------|----------|
| P0-1 | **知识条目 CRUD 端点缺失** | 知识库管理页的"我的知识"和"知识库" Tab 无法正常加载，始终降级到空缓存 | 需要新增 `routers/knowledge.py` 中的 `GET /entries`、`GET /entries/{id}`、`POST /entries/{id}/offline` |
| P0-2 | **Dashboard 统计端点缺失** | 工作台统计数据（今日提问、知识条目数、今日审批）无后端数据源 | 需要新增 dashboard 路由或从现有端点聚合 |
| P0-3 | **UnansweredQuestion 写入机制缺失** | 高频待补问题列表可能永远为空——没有代码将拒答写入 `unanswered_questions` 表 | `routers/chat.py` 或 `services/refusal.py` 中需对接写入逻辑 |

### P1 — 影响用户体验

| # | 问题 | 影响 | 修复文件 |
|---|------|------|----------|
| P1-1 | **timeout 超时回退未实现** | pending_teacher 状态无限等待，如果教师离线，会话永久卡在"待处理" | `state_machine.py` + 定时任务/调度器 |
| P1-2 | **知识条目编辑功能为空** | detail.vue 点击编辑显示"开发中" | `pages/knowledge/detail.vue` + 后端编辑端点 |
| P1-3 | **已下线条目无后端端点** | 前端调用 `/api/v1/knowledge/entries/{id}/offline` 但后端不存在 | `routers/knowledge.py` |
| P1-4 | **废弃 escalation.ts 未清理** | 存在死代码（v1 端点），可能误导后续开发者 | `api/escalation.ts` |

### P2 — 优化与完善

| # | 问题 | 影响 | 修复文件 |
|---|------|------|----------|
| P2-1 | **WS send_message 不写库** | 代码注释标注为临时方案，需改为 HTTP API 方式保证事务性 | `routers/ws.py` L91-106 |
| P2-2 | **无消息回执/已读状态** | 教师无法知道学生是否已读回复 | `models/conversation.py` Message 表 + 逻辑 |
| P2-3 | **学生端未读计数器教师不可用** | 教师端无法获取自己对话的未读消息 | `conversation_service.py:72-73` |
| P2-4 | **本地缓存降级可能造成数据不一致** | knowledge.ts 的 .catch() fallback 在审批时模拟成功，实际可能未生效 | `knowledge.ts` approveKnowledge/rejectKnowledge |
| P2-5 | **班级/学院知识无需审批直接发布** | 设计意图明确但存在质量风险 | `knowledge_service.py` `create_knowledge_draft` |

---

## 六、架构建议

### 6.1 结论：继续修补，不引入成熟方案

**理由**：

1. **核心流程已完整**: 工单处理的完整闭环（创建→AI→转人工→教师回复→解决）全部打通，WebSocket 实时通信也已实现。
2. **技术栈纯度高**: FastAPI + PostgreSQL + Dify 的架构统一、简洁，引入 ByteDesk/Chatwoot 会带来 Java/Ruby 异构依赖、维护负担和部署复杂度。
3. **差距可控**: 主要缺失的是 CRUD 端点（知识条目列表/详情/下线）和统计聚合，这些是 1-2 天的工作量，而非架构级问题。
4. **历史决策支持**: v1 团队已做过充分调研并明确决定不走平台迁移路线。

### 6.2 补全路线图

**第一阶段 (1-2 天): 补 P0 缺口**
- 新增 `GET /api/v1/knowledge/entries` — 分页查询 KbSuggestion（按用户角色过滤）
- 新增 `GET /api/v1/knowledge/entries/{id}` — 知识条目详情
- 新增 `POST /api/v1/knowledge/entries/{id}/offline` — 将条目状态改为 offline（新增 SuggestionStatus.offline）
- 新增 `GET /api/v1/dashboard/stats` — 从聚合查询返回今日提问/知识条目/审批数
- 实现拒答写入 `unanswered_questions` 逻辑

**第二阶段 (2-3 天): 修 P1 问题**
- 实现 timeout 调度器（定时任务检查 pending_teacher 超时会话）
- 实现知识条目编辑端点
- 清理 `escalation.ts` 死代码
- WS send_message 改为 HTTP API + WS 通知模式

**第三阶段 (3-5 天): P2 优化**
- 消息回执系统（delivered_at / read_at）
- 教师端未读计数器
- 审批流程完整性加固
- 端到端集成测试

### 6.3 总体评分

| 模块 | 评分 | 说明 |
|------|------|------|
| 工单处理核心流 | 85% | 状态机+WS+API 完整，缺 timeout 回退和消息回执 |
| 知识入库流程 | 60% | 草稿→审核→发布路径畅通，但条目管理和展示断裂 |
| 教师工作台 | 40% | 有 UI 无数据（统计端点缺失），快捷操作多为占位符 |
| 整体教师端 | **65%** | 核心流程可用，知识管理半成品，看板需要后端补全 |
