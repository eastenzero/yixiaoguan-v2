# 医小管 开发计划 v2（2025-04-12 深度扫描版）

> 本文档由 Cascade 深度扫描全量代码后产出，供团队决策参考。
> 在对话中确认最终方向后再出具体 spec。

---

## 一、项目架构总览

```
yixiaoguan/
├── apps/
│   ├── student-app/       # UniApp 学生端（已基本可用）
│   ├── teacher-app/       # UniApp 教师移动端（有 params bug）
│   └── teacher-web/       # Vue3 + ElementPlus 教师网页端（框架+UI已搭建，登录未通）
├── services/
│   ├── ai-service/        # Python FastAPI（RAG + Intent Agent）
│   └── business-api/      # Java Spring Boot（若依框架）
└── knowledge-base/        # 知识库 Markdown 文件
```

### 后端业务模块一览（business-api 下 com.yixiaoguan.*）

| 模块 | 说明 | 完成度 |
|------|------|--------|
| `ai/` | AiCoordinatorService — 意图识别 + 分支调度 + 流式推送 | ✅ 代码完整，但前端**未接入** |
| `aipersona/` | AI 人设配置 | 待查 |
| `auditlog/` | 审计日志 | 待查 |
| `auth/` | 认证 | ✅ |
| `classroom/` | 教室申请 CRUD + 审批 | ✅ |
| `conversation/` | 会话 + 消息 + 工单（Escalation） | ✅ |
| `dashboard/` | 教师工作台聚合统计（**真实 SQL，非 mock**） | ✅ |
| `knowledge/` | 知识库管理 | ✅ |
| `notification/` | 站内通知（**后端 100% 完成，前端 0% 对接**） | 后端 ✅ / 前端 ❌ |
| `pushtask/` | 批量推送任务（**后端 100% 完成，前端 0% 对接**） | 后端 ✅ / 前端 ❌ |
| `quicklink/` | 快捷链接 | 待查 |
| `user/` | 用户管理 | ✅ |
| `websocket/` | WebSocket 消息处理 | ✅ |

---

## 二、关键发现（深度扫描结果）

### 🔴 发现 1：学生端 AI 对话绕过了后端智能管线

**现状**：
- 学生端 `chat/index.vue` 直接 `fetch('/api/chat/stream')` 调 Python AI 服务
- 消息通过 HTTP `POST /api/v1/conversations/{id}/messages` 保存
- AI 回复**不经过 Java 层**

**后端已建好但未被使用的完整管线**：
```
WebSocket → YxChatWebSocketHandler → AiCoordinatorServiceImpl
  ├─ 步骤1: 调 Python /api/agent/extract 做意图识别
  ├─ 分支A: 普通聊天 → 流式 RAG（带最近 6 条历史上下文）
  ├─ 分支B: book_classroom → classroomAppService.submitApplication()（已实现！）
  ├─ 分支C: submit_repair_request → 官网兜底（预留）
  └─ 分支D: query_application_status → 官网兜底（预留）
```

**影响**：
- 意图识别 + 对话式教室预约 → 完全没用上
- 消息落库可能不一致（AI 回复未经 Java 存库）
- 教师实时介入的 WebSocket 通道断开

### 🔴 发现 2：通知系统已 100% 建好但 0% 对接

| 组件 | 状态 |
|------|------|
| `YxNotificationController`（列表、详情、标已读、全部已读、删除） | ✅ 后端完整 |
| `YxNotificationServiceImpl` | ✅ 后端完整 |
| `YxPushTaskController`（创建、发送、取消、删除） | ✅ 后端完整 |
| `YxPushTaskServiceImpl`（支持全体/指定班级/指定用户三种目标） | ✅ 后端完整 |
| `student-app/api/notification.ts`（getNotificationList, getUnreadCount, markAsRead） | ✅ API 定义有 |
| **学生端通知页面** | ❌ 不存在，所有🔔按钮 = `showDevToast` |
| **教师端推送管理入口** | ❌ 不存在 |

### 🟡 发现 3：教师网页端 Dashboard 是真实数据

`DashboardServiceImpl`（297 行）直接用 JdbcTemplate 查数据库：
- 今日提问数 + 同比昨日增长率
- 待审批教室申请（含超 48 小时紧急标记）
- AI 自动解决率 = AI 回复数 / 学生提问数
- 平均响应时间（分钟）
- 高频问题 TOP5（按 question_summary GROUP BY）
- AI 舆情预警（关键词 7 日 vs 14 日趋势）

`QuestionsView.vue` 也做了真实 API 调用 + 字段适配器，只有 `getQuestionStats()` 一个接口兜底 mock。

### ~~🟡 发现 4：教师移动端 params bug~~ → 已修复

~~`teacher-app` 的 `escalation.ts` / `knowledge.ts` 用 `request({ params: {...} })`~~
→ 复查发现 `request.ts` 第 22-32 行**已处理** params → query string 转换，此 bug **不存在**。

### 🟢 发现 5：AI 意图识别已完整实现

Python 端 `IntentExtractor` + Java 端 `IntentType` 枚举 + `AiCoordinatorServiceImpl` 分支路由。
支持的意图：
- `CHAT` — 普通聊天 → RAG
- `BOOK_CLASSROOM` — 预约教室 → 自动提交申请（**含多轮追问缺失参数**）
- `SUBMIT_REPAIR_REQUEST` — 设备报修 → 兜底
- `QUERY_APPLICATION_STATUS` — 查询进度 → 兜底

### 🟢 发现 6：工单（Escalation）后端闭环完整

后端链路：学生呼叫 → 创建工单 → 教师查看待处理 → 认领 → 回复解决 → 关闭。
前端链路缺失：学生看不到教师的回复（通知未接通）。

---

## 三、教务系统对接 & 企微部署方案（2025-04-12 讨论结论）

### 背景变更
老师决定**不做教务系统实际逻辑对接**，只做快捷入口跳转。

### 3.1 快捷入口方案对比

| 方案 | 免登跳转 | 含金量 | 可行性 | 说明 |
|------|---------|--------|--------|------|
| **A: 纯 HTTP 链接** | ❌ 需登录信息门户 | 低 | ✅ 极简 | 没有技术门槛，用户体验差 |
| **B: 微信小程序 + 绑企微** | ❌ 不行 | — | ❌ | 微信 OpenID ≠ 企微身份，SSO 会话不互通 |
| **C: 部署为企微自建应用/企微小程序** | ✅ 免登 | 高 | ✅ 可行 | 企微内 wx.qy.login() 拿身份，deep-link 到工作台其他应用 |
| **D: 企微 H5 应用** | ✅ 免登 | 高 | ✅ 可行 | UniApp 编译为 H5，嵌入企微工作台 |

### 3.2 企微验证结果（2025-04-12）

已验证：学校企微工作台的应用（信息门户、网上报修等）点击后**自动加载并跳转**，不弹登录页。
→ 说明学校已做企微 SSO 深度集成，快捷跳转方案可行。

### 3.3 推荐架构：企微机器人 + 轻量 H5（最终方案）

直接在企微里做一个完整 app 页面会**重复工作台布局**，因此采用"机器人 + H5"组合：

```
企业微信
  ├── 医小管（自建应用）
  │     ├── 消息回调 → AI 问答 + 意图识别 + 服务卡片路由  ← 机器人能力
  │     │     学生发消息"空调坏了" → 识别 SUBMIT_REPAIR_REQUEST
  │     │     → 回复图文卡片，点击直接跳到企微"网上报修"（免登）
  │     │
  │     └── 应用主页 → H5 页面（UniApp 编译）  ← 需要完整 UI 的功能
  │           ├── 通知列表
  │           ├── 我的工单
  │           ├── 对话历史
  │           └── 个人中心
  │
  └── 学校已有应用（卡片跳转目标）
        ├── 信息门户
        ├── 网上报修
        ├── 接诉即办
        └── ...
```

**核心优势**：
- 现有的 `IntentExtractor`（Python）+ `AiCoordinatorServiceImpl`（Java）天然就是机器人大脑
- 意图识别输出从"文字回复"改为"图文卡片" = 快捷入口能力
- 不重复工作台布局，学生在聊天里直接说需求即可
- 需要完整 UI 的功能（工单、通知等）放在应用主页 H5 中

### 3.4 企微开发前置条件

| 条件 | 状态 | 说明 |
|------|------|------|
| 企微管理后台权限 | ❌ 需申请 | 创建自建应用需管理员或子管理员权限 |
| `corpId` + `agentId` + `secret` | ❌ 待创建 | 创建应用后获取 |
| 消息回调 URL（公网可达） | ❌ 待部署 | 后端需部署到公网并配置企微回调 |

### 3.5 开发策略：先核心后适配

**阶段 1（当前）**：在现有 UniApp 学生端把核心功能做扎实
- 接通 AiCoordinator 管线
- 工单闭环
- 通知系统
- → 这些功能跟最终部署在微信还是企微无关

**阶段 2（拿到企微权限后）**：适配企微
- 登录方式改为 `wx.qy.login()`
- AI 回复增加图文卡片格式
- 快捷入口映射到企微工作台应用
- UniApp 条件编译区分企微 vs 普通微信

**好处**：不被管理员权限卡住，先出效果再跟老师谈权限

---

## 四、修正后优先级方案

> ⚠️ 以下排序综合"投入产出比 + 演示效果 + 技术依赖"，待团队确认后执行。
> 整体策略：**阶段 1 先做核心功能（与企微无关），阶段 2 拿到权限后适配企微。**

### 阶段 1：核心功能（当前，不依赖企微权限）

#### P0（最高优先，应立即做）

| # | 任务 | 工作量 | 价值 |
|---|------|--------|------|
| ~~P0-1~~ | ~~修复教师移动端 params bug~~ | — | 复查发现已修复，跳过 |
| P0-2 | **学生端接入 AiCoordinator 管线** | 中 | 解锁意图识别、消息一致性、教师介入基础；意图识别到办事类请求时回复引导文案+链接（为阶段 2 企微卡片做铺垫） |

#### P1（高优先，P0 后紧跟）

| # | 任务 | 工作量 | 价值 |
|---|------|--------|------|
| P1-1 | **学生端通知页面**（后端 API 全齐，只需写前端页面） | 小 | 打通通知闭环 |
| P1-2 | **工单闭环最后一环**：学生看到教师回复 | 小 | 核心演示闭环 |
| P1-3 | **teacher-web 登录对接** | 中 | Dashboard 真实数据可展示 |

#### P2（中优先）

| # | 任务 | 工作量 | 价值 |
|---|------|--------|------|
| P2-1 | 教师端推送管理 UI（后端 PushTask 全齐） | 中 | 教师群发通知 |
| P2-2 | AI 自动上报（拒答 → 自动创建工单） | 小 | 减少学生手动呼叫 |
| P2-3 | AI 对话体验优化（来源引用、快捷问题、样式） | 中 | 体验提升 |

#### P3（低优先 / 后期）

| # | 任务 | 工作量 | 价值 |
|---|------|--------|------|
| P3-1 | 知识库扩量 + 防幻觉强约束 | 持续 | AI 质量 |

### 阶段 2：企微适配（拿到管理员权限后）

| # | 任务 | 工作量 | 前置条件 |
|---|------|--------|---------|
| W1 | 企微管理后台创建自建应用，获取 corpId/agentId/secret | 小 | 管理员权限 |
| W2 | 后端增加企微消息回调接口（接收用户消息 → AiCoordinator） | 中 | W1 |
| W3 | AI 回复增加图文卡片格式（办事意图 → 返回企微 news 卡片） | 小 | W2 |
| W4 | 映射学校企微工作台应用 URL，配置快捷跳转目标 | 小 | W1 |
| W5 | UniApp 编译 H5 作为应用主页（通知、工单、历史等完整 UI） | 中 | W1 |
| W6 | 登录方式适配 `wx.qy.login()` + 条件编译 | 中 | W1 |

---

## 五、已放弃 / 暂缓事项

| 事项 | 原因 |
|------|------|
| 教务系统实际逻辑对接（教室申请提交、报修提交等） | 老师决定改为链接跳转，不做实际集成 |
| AI 对话中触发教室预约的完整业务流（AiCoordinator.handleBookClassroom） | 教务不做实际对接，此路径价值降低；意图识别框架保留，办事意图改为回复引导文案+链接 |
| 根据回复内容智能推荐相关链接/入口 | 当前暂缓，不在本轮范围 |
| 企微适配（机器人+H5） | 阶段 2 做，需先拿到管理员权限；当前阶段核心功能与企微无关 |
| 教室申请审批页面（教师 Web） | 教务不做实际集成后，审批页面非必需；降为 P3 或放弃 |

---

## 六、关键文件索引（方便后续开发快速定位）

### 学生端
- 聊天页：`apps/student-app/src/pages/chat/index.vue`
- Chat API：`apps/student-app/src/api/chat.ts`
- 通知 API（已定义未使用）：`apps/student-app/src/api/notification.ts`
- 申请 API：`apps/student-app/src/api/apply.ts`
- 首页：`apps/student-app/src/pages/home/index.vue`
- 服务页：`apps/student-app/src/pages/services/index.vue`
- 我的问题：`apps/student-app/src/pages/questions/index.vue`

### 教师移动端
- 工单 API（有 params bug）：`apps/teacher-app/src/api/escalation.ts`
- 知识库 API（有 params bug）：`apps/teacher-app/src/api/knowledge.ts`
- 问题列表：`apps/teacher-app/src/pages/questions/index.vue`
- 问题详情：`apps/teacher-app/src/pages/questions/detail.vue`

### 教师网页端
- Dashboard：`apps/teacher-web/src/views/DashboardView.vue`
- 问题管理：`apps/teacher-web/src/views/QuestionsView.vue`
- API 层：`apps/teacher-web/src/api/` (dashboard.ts, questions.ts, knowledge.ts, approval.ts, auth.ts)

### 后端核心
- AI 协调器：`services/business-api/.../ai/service/impl/AiCoordinatorServiceImpl.java`
- AI 客户端：`services/business-api/.../ai/client/AiServiceClient.java`
- 意图枚举：`services/business-api/.../ai/enums/IntentType.java`
- 工单 Controller：`services/business-api/.../conversation/controller/EscalationController.java`
- 工单 Service：`services/business-api/.../conversation/service/impl/YxEscalationServiceImpl.java`
- WebSocket 处理器：`services/business-api/.../websocket/handler/YxChatWebSocketHandler.java`
- 通知 Controller：`services/business-api/.../notification/controller/YxNotificationController.java`
- 推送任务 Controller：`services/business-api/.../pushtask/controller/YxPushTaskController.java`
- Dashboard Service：`services/business-api/.../dashboard/service/impl/DashboardServiceImpl.java`

### AI 服务
- RAG Chat：`services/ai-service/app/api/chat.py`
- Agent Intent：`services/ai-service/app/api/agent.py`
- Intent Extractor：`services/ai-service/app/core/intent_extractor.py`
- LLM Chat Engine：`services/ai-service/app/core/llm_chat.py`
