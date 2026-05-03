# 2026-05-03 冒烟测试问题分析报告

> 基于 `.tasks/hk-deploy/full-smoke-report-2026-05-03.md` 的逐项验证

## 一、各问题验证结论

### Issue 1: Gateway `/health` 返回前端 HTML ✅ 真实存在

**根因**：nginx `location /` 带 SPA fallback `try_files $uri $uri/ /index.html`，会把 `/health` 也 catch 住返回前端 HTML。而 `/api/` location 代理到 gateway `127.0.0.1:8100`，但 gateway 的 health 端点注册在根路径 `@app.get("/health")`，不在 `/api/health`。

- `GET /health` → nginx SPA fallback → 前端 index.html
- `GET /api/health` → proxy 到 gateway → gateway 没有 `/api/health` 路由 → 404

**修复方案**：nginx 添加 `location = /health` 精确匹配，proxy_pass 到 gateway。

---

### Issue 2: 教师工作台待处理不实时刷新 ✅ 真实存在（双重根因）

**根因 A —— 前端代码缺陷**：`teacher-app/src/pages/dashboard/index.vue` 只在 `onMounted` 和 `onShow` 加载数据，**没有注册任何 WebSocket 监听器**。对比 `questions/index.vue` 已经正确监听了 `escalation_notify` 和 `status_changed`。

**根因 B —— 多 Worker 架构缺陷**（见 Issue 3 详解）

**修复方案**：
- dashboard 页面添加 WS `escalation_notify` / `status_changed` 监听
- 配合 Issue 3 的 workers 修复

---

### Issue 3: 学生当前页未实时显示老师回复 ✅ 真实存在（架构级 Bug）

**学生端代码本身是正确的**。`chat/index.vue` 正确注册了 `new_message` 和 `status_changed` 监听，`onNewMessage` 正确判断 `sender_type === 'teacher'` 并 push 到消息列表。

**真正的根因是 `--workers 2`**：

Gateway systemd 配置 `ExecStart=... --workers 2`，uvicorn 多 worker 使用 multiprocessing，每个 worker 有独立的 `ConnectionManager` 实例。WebSocket 连接绑定在某个 worker 上，而 HTTP 请求由 OS 负载均衡分配。

教师"回复并解决"实际触发两个顺序 HTTP 请求：
1. `POST /{conv_id}/messages` → 写库 + broadcast `new_message`
2. `POST /{conv_id}/resolve` → 状态机 + broadcast `status_changed`

两个请求可能落在不同 worker 上。如果学生 WS 连接在 worker A：
- 请求 1 落在 worker B → broadcast 在 B 的 ConnectionManager → 学生收不到 `new_message`
- 请求 2 落在 worker A → broadcast 在 A 的 ConnectionManager → 学生收到 `status_changed`

这完美解释了报告中的现象："学生当前页实时显示'问题已解决'，但没有实时显示老师回复文本。"

**修复方案**：`--workers 1`。当前用户规模（内测阶段）单 worker 完全足够。长期可引入 Redis pub/sub 跨 worker 广播。

---

### Issue 4: 静态资源 404 ✅ 真实存在

**Manrope 字体**：两端 `App.vue` 都硬编码引用 `https://fonts.gstatic.com/s/manrope/...`。Google Fonts CDN 在国内可能不可达或不稳定。

**teacher favicon.ico**：整个项目没有任何 `favicon.ico` 文件，浏览器默认请求 `/favicon.ico` 必然 404。

**修复方案**：
- 字体：下载 woff2 文件自托管到 `static/fonts/`
- favicon：创建或放置 `.ico` 文件到各端 `public/` 目录（构建后产出到 dist 根目录）

---

### Issue 5: 知识库测试草稿残留 ⚠️ 运维清理项

不是代码 bug，是测试数据残留。需手动在 Dify 和数据库清理 entry.id=7。

长期应添加管理员知识条目下线/删除 API，但不在本轮修复范围。

---

## 二、额外发现

### 发现 1: 多 Worker 是 Issue 2 + Issue 3 的共同根因

同一个架构缺陷同时造成了教师端和学生端的 WebSocket 广播不可靠。修复 workers 后两个问题的 WS 传输层同时解决。

### 发现 2: 教师工作台统计数据不准确

`dashboard/index.vue` 的 `loadStats` 用 `listConversations(1, 1)` 取 `total` 作为"今日提问"数，实际是全量会话总数，不是今日数。此问题不在冒烟报告中但值得修复。

### 发现 3: nginx 嵌套 location 缺少闭合括号

`yxg-student-domain` 配置中 `location /` 内嵌套了 `location ~*` 和 `location /ws`、`location /api/` 但缺少 `}` 闭合。nginx 可能自行容错解析通过了，但这是不规范配置，有潜在风险。

---

## 三、修复优先级评估

| # | 问题 | 报告优先级 | 我的评估 | 理由 |
|---|------|-----------|---------|------|
| 1 | 多 Worker 导致 WS 广播丢失 | P1 (#3) | **P0** | 架构级根因，同时影响 Issue 2 + 3 |
| 2 | 教师工作台无 WS 监听 | P2 (#2) | **P1** | 即使修了 workers，dashboard 仍需代码改动 |
| 3 | nginx health 端点 | P1 (#1) | **P1** | 监控/运维需要 |
| 4 | 字体 & favicon 404 | P3 (#4) | **P2** | 影响用户体验和控制台清洁度 |
| 5 | 测试数据清理 | P2 (#5) | **P3** | 一次性运维操作 |
