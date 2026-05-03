# 新域名完整冒烟测试报告（2026-05-03）

## 基本信息

- 测试时间：2026-05-03 19:29:43 +08:00
- 目标环境：
  - 学生端：https://yxg.xiaoguan.site/
  - 教师端：https://teacher.xiaoguan.site/
  - Dify Console：https://dify.xiaoguan.site/
- 测试账号：
  - 学生：`4125150001` / 黄静
  - 辅导员：`anjing` / 安静
- 测试方式：
  - Python requests：API 冒烟、SSE、知识库、证书、WebSocket ping/pong、HTTP Upgrade
  - Playwright CLI：学生端/教师端真实 UI 流程

## 复测更新（2026-05-03 20:27:43 +08:00）

针对上轮失败项完成复测，核心问题已修复：

| 复测项 | 结果 | 证据 |
|---|---|---|
| Gateway `/health` | PASS | `https://yxg.xiaoguan.site/health` 返回 `{"status":"ok","version":"2.0.0","checks":{"postgres":"ok","redis":"ok","dify":"ok"}}` |
| 教师工作台实时刷新 | PASS | 学生转人工后，教师工作台无需刷新即显示“今天有 1 条待处理提问”，待处理列表出现 `【retest-20260503】请帮我` |
| 学生当前页老师接入推送 | PASS | 教师接单后，学生当前页实时显示“老师已接入，你可以直接向老师提问。” |
| 学生当前页老师回复推送 | PASS | 教师回复并解决后，学生当前页实时显示“老师回复：复测通过：老师回复应实时展示。” |
| 学生当前页解决状态推送 | PASS | 同一当前页实时显示“问题已解决。如有新问题，可继续提问。” |
| 浏览器控制台错误 | PASS | 本次学生端/教师端 Playwright 控制台 error 均为 0 |
| 测试会话清理 | PASS | 会话 `id=41` 已 close |

复测结论：新域名核心 API、Gateway health、教师工作台实时待处理、学生当前页老师回复实时推送均已通过。本轮复测可以输出：`新域名完整冒烟测试全部通过，可以继续内测/上线验证`。

仍需运维/后台确认的历史残留：上轮知识库测试草稿 `entry.id=7` / Dify 文档 `4884e802-c199-4018-b4e0-0ddfe379ab2f` 是否需要清理。

## 初测结论（历史记录）

新域名主业务链路大部分可用，但本轮不是全绿，暂不建议直接判定“完整冒烟全部通过”。

主要阻塞/风险：

1. `https://yxg.xiaoguan.site/health` 返回学生端 HTML，不是 Gateway health；`https://yxg.xiaoguan.site/api/health` 返回 404。
2. 教师工作台在学生转人工后没有实时刷新待处理数量/列表；进入“学生提问”列表后能看到待处理。
3. 学生当前聊天页能实时收到“老师已接入”和“问题已解决”，但没有实时显示老师回复；刷新后从历史会话进入可以看到老师回复。
4. 浏览器控制台存在静态资源 404：Manrope 字体、教师端 favicon。
5. 知识库草稿测试创建并发布了测试数据 `entry.id=7`，当前未发现公开删除/下线接口，需要后台清理确认。

## 汇总表

| 测试项 | 结果 | 备注 | 证据 |
|---|---|---|---|
| 学生端首页可达 | PASS | HTTP 200 | `https://yxg.xiaoguan.site/` 返回 HTML |
| 教师端首页可达 | PASS | HTTP 200 | `https://teacher.xiaoguan.site/` 返回 HTML |
| Dify Console 可达 | PASS | HTTP 200 | 最终跳转到 `https://dify.xiaoguan.site/apps` |
| HTTPS 证书 | PASS | SAN 覆盖 3 个域名 | `yxg.xiaoguan.site`、`teacher.xiaoguan.site`、`dify.xiaoguan.site`，到期 `Jul 30 13:48:19 2026 GMT` |
| Gateway `/health` | FAIL | 新域名未暴露正确健康检查 | `/health` 返回前端 HTML；`/api/health` 返回 `{"detail":"Not Found"}` |
| 学生登录 | PASS | HTTP 200 | `/api/auth/login` 返回 token，`/api/auth/me` name=`黄静` |
| 辅导员登录 | PASS | HTTP 200 | `/api/auth/login` 返回 token，`/api/auth/me` name=`安静` |
| RAG：宿舍电费 | PASS | 命中质量规则 | 回答包含“完美校园/充值” |
| RAG：国家奖学金 | PASS | 命中质量规则 | 回答包含“10000/奖学金” |
| RAG：图书馆开放时间 | PASS | 命中质量规则 | 回答非空且长度 > 50 |
| API 转人工闭环 | PASS | 创建、转交、接单、回复、解决、学生查看均通过 | 会话 `id=39`，最终已关闭 |
| 未读统计 | PASS | HTTP 200 | 学生端 unread-summary 返回对应未读项 |
| 知识库未回答排行 | PASS | HTTP 200 | 返回未回答问题列表 |
| 知识库提交草稿 | PASS（有残留风险） | HTTP 201 | 创建 `entry.id=7`，`dify_document_id=4884e802-c199-4018-b4e0-0ddfe379ab2f` |
| WebSocket 学生域名 ping/pong | PASS | WSS 正常 | `wss://yxg.xiaoguan.site/ws?token=...` 返回 `{"type":"pong"}` |
| WebSocket 教师域名 ping/pong | PASS | WSS 正常 | `wss://teacher.xiaoguan.site/ws?token=...` 返回 `{"type":"pong"}` |
| WebSocket 学生域名 Upgrade | PASS | NGINX 反代正常 | HTTP `101 Switching Protocols` |
| WebSocket 教师域名 Upgrade | PASS | NGINX 反代正常 | HTTP `101 Switching Protocols` |
| UI 学生登录 | PASS | 进入首页 | 页面显示“下午好，黄静” |
| UI 学生提问/转人工 | PASS | 当前页进入等待老师状态 | 显示“已通知老师，请耐心等待回复。” |
| UI 教师待处理入口 | PARTIAL | 学生提问列表可见，工作台未实时刷新 | 工作台仍显示 0；进入“学生提问”列表显示待处理 1 |
| UI 教师接单 | PASS | 学生当前页实时收到接入 | 学生页显示“老师已接入，你可以直接向老师提问。” |
| UI 教师回复并解决 | PARTIAL | 后端和教师端有回复，学生当前页只实时收到解决状态 | 学生当前页未出现“完整冒烟 UI：老师已接入并实时回复。” |
| UI 历史会话展示 | PASS | 刷新后从历史进入可见完整内容 | 显示“老师回复：完整冒烟 UI：老师已接入并实时回复。” |
| 控制台错误 | PARTIAL | 无 WebSocket 错误，有资源 404 | `fonts.gstatic.com/...Manrope...woff2` 404；`teacher.xiaoguan.site/favicon.ico` 404 |

## 失败项详情

### 1. Gateway 健康检查未正确暴露

- 复现步骤：
  - GET `https://yxg.xiaoguan.site/health`
  - GET `https://yxg.xiaoguan.site/api/health`
- 实际结果：
  - `/health` 返回 HTTP 200，但 body 是学生端 HTML。
  - `/api/health` 返回 HTTP 404，body 为 `{"detail":"Not Found"}`。
- 期望结果：
  - 应有一个明确的 Gateway health endpoint 返回 JSON，例如 `{"status":"ok"}`。
- 初步归因：
  - NGINX 对 `/health` 走了前端 SPA fallback；Gateway 当前没有通过新域名暴露健康检查，或路径未配置。

### 2. 教师工作台待处理数量/列表未实时刷新

- 复现步骤：
  - 教师端保持在工作台。
  - 学生端发起 `【full-smoke-20260503】请帮我转人工` 并点击“转人工服务”。
  - 不刷新教师工作台，观察待处理数量。
- 实际结果：
  - 工作台仍显示“今天有 0 条待处理提问”，待处理卡片为空。
  - 点击进入“学生提问”列表后，能看到待处理 1 和对应会话。
- 期望结果：
  - 教师工作台应实时显示新增待处理，或至少有明确刷新机制。
- 初步归因：
  - WebSocket 基础连接正常，可能是教师工作台未订阅/处理待处理列表刷新事件，或只在页面加载时请求数据。

### 3. 学生当前页未实时显示老师回复

- 复现步骤：
  - 学生端保持当前聊天页不刷新。
  - 教师端接单后输入“完整冒烟 UI：老师已接入并实时回复。”并点击“回复并解决”。
- 实际结果：
  - 学生当前页实时显示“问题已解决。如有新问题，可继续提问。”
  - 学生当前页没有实时显示老师回复文本。
  - 后端 `/api/conversations/40/messages` 存在 teacher 消息 `id=253`。
  - 教师端详情页存在该老师回复。
  - 学生刷新后从历史会话进入，也能看到该老师回复。
- 期望结果：
  - 学生当前页在不刷新情况下同时出现“老师回复”和“问题已解决”。
- 初步归因：
  - WebSocket status_changed 已到达；teacher new_message 事件可能未发到学生房间，或学生端消息事件处理/渲染对 teacher 消息有遗漏。

### 4. 静态资源 404

- 学生端控制台：
  - `https://fonts.gstatic.com/s/manrope/v15/xn7_YHE41ni1AdIRqAuZuw1Bx9mbZk59FO_F87jxeN7B.woff2` 404
- 教师端控制台：
  - 同 Manrope 字体 404
  - `https://teacher.xiaoguan.site/favicon.ico` 404
- 影响：
  - 不影响本轮主流程，但会污染控制台并可能影响字体观感/浏览器错误监控。

## 清理记录

| 类型 | ID | 最终状态 | 备注 |
|---|---:|---|---|
| API RAG 会话 | 38 | closed | 已清理 |
| API 转人工会话 | 39 | closed | 已清理 |
| UI 转人工会话 | 40 | closed | 已清理 |
| 知识库测试草稿 | 7 | published/approved | 未发现公开删除/下线接口，需后台清理 |

## 建议优先级

1. P1：修复学生当前页 teacher message 实时展示。
2. P1：修复或明确新域名 Gateway health endpoint。
3. P2：教师工作台增加待处理实时刷新，或收到转人工事件后自动重新拉取列表。
4. P2：清理知识库测试草稿 `entry.id=7` / Dify 文档 `4884e802-c199-4018-b4e0-0ddfe379ab2f`。
5. P3：修复字体和 favicon 404。

## 最终结论

新域名 API 主流程、RAG、WebSocket 基础连接、学生/教师 UI 闭环的数据持久化均可用；但仍存在实时 UI 展示和健康检查暴露问题。

本轮不能输出“新域名完整冒烟测试全部通过，可以继续内测/上线验证”。建议修复上述 P1 项后再跑一轮完整冒烟。
