# Kimi 派单 · T11 + T12 + T13 · 三段 demo 录制

> 2026-05-11 23:55 导演产出（Cascade）
> 派给 Kimi。完成后回报三个 webm + 三个 events.json。

---

## 项目上下文（一句话）

医小管演示视频 Phase 2 录制阶段。前置全部就绪：UI 已 commit (0d2abe2)、demo 数据 seeded、Centrifugo 实时推送通道已验证。三段录制脚本骨架已落地，本任务负责跑 + 填实际 DOM selector。

## 工作目录

```
F:\Documents\code\yixiaoguan-v2
```

## 前置依赖（已就绪）

- ✅ UI commit `0d2abe2` on `fix/realtime-user-channel-push`
- ✅ 学生端截图 `.tasks/student-ui-audit-2026-05-11/after-avatar/` 7 张 PNG
- ✅ 教师端截图 `.tasks/teacher-ui-audit-2026-05-11/after-avatar/` 11 张 PNG
- ✅ demo seed 数据（[demo] 标记工单 30+ / KB 25 条 / unanswered 8 条）
- ✅ dev server: student `:3001` + teacher `:5301` 在线
- ✅ 165 dev backend `http://192.168.100.165:8100` 在线（anjing/4125150011/A001 可登录）
- ✅ Centrifugo via SSH tunnel `localhost:18000`（已开，别关）

## 共同测试账号

- 学生：`4125150011` / `4125150011`
- 教师：`anjing` / `Anjing@yxg2026`
- token key：学生 `v2-token` / `v2-user-info`，教师 `teacher-token` / `teacher-user-info`

---

## 任务 1 · T11 · D1 学生端录制（70s，先做）

### 脚本

`@F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\record-d1-student.mjs`

### 执行

```powershell
cd F:\Documents\code\yixiaoguan-v2
node .tmp/demo-video/record-d1-student.mjs
```

### 预期输出

```
.tmp/demo-video/out/d1/
├── student.webm      (~70s, 393×852)
├── events.json
└── frames/           (关键时间点 PNG 缩略图)
```

### 镜头脚本（剧本 04 §2.3）

| 起-止 | 时长 | 操作 | 关键 |
|---|---|---|---|
| 0-8s | 8s | 登录页 → 输入学号 → 跳 home | 用 login → home 自动重定向 |
| 8-16s | 8s | home 浏览 | hero / chips / 服务卡 |
| 16-32s | 16s | **点 chip『宿舍电费怎么交？』** → AI 流式答 | **不要手动 fill** — chip onTagClick 自动写 chat_init_query + switchTab，chat onMounted 自动发问 |
| 32-42s | 10s | 来源弹层 → 关闭 → 历史 | TODO selector，跑不通就跳过 |
| 42-54s | 12s | 提复杂问题 → 转人工 | fill input + click 发送 + click 转人工 |
| 54-70s | 16s | 等待 + buffer | 学生屏静止显示『等待老师』 |

### 已知坑（chat 进入）

学生端 chat/index.vue 的 onShow 从 `localStorage.pendingConversationId` 读 convId，**不认 URL query**。脚本里已经避开（直接点 chip 触发 chat_init_query），不需要再处理。详见 chat/index.vue:336-348。

### 跑不通时的 selector 调试

脚本里 TODO 处需要根据真实 DOM 微调，跑一遍 `headless: false` 看哪个 click 失败，DevTools 选元素重定位：

| 步骤 | 当前 selector | 调试方法 |
|---|---|---|
| chip『宿舍电费怎么交』 | `text=宿舍电费怎么交` | 若多匹配，用 `.tag-chip:has-text("宿舍电费")` |
| 输入框 | `textarea, .chat-input textarea, [placeholder*="问题"]` | DevTools 选实际 input 看 class |
| 发送按钮 | `button:has-text("发送"), .send-btn` | 可能是 icon-only 用 `[aria-label="发送"]` |
| 来源/历史/转人工 | `text=...` 系列 | 如不存在不报错也行（脚本已 catch） |

### 验收

- ☐ `out/d1/student.webm` 文件大小 > 3 MB（< 1 MB 说明大部分录到黑屏）
- ☐ `events.json` 中 events 数量 > 15
- ☐ events.json 里有 `type: "ai_streaming_start"` 和 `type: "ai_streaming_end"`（流答采样跑了）
- ☐ 视觉抽检：webm 里能看到 home → chat 流答 → 转人工等待 三段画面

---

## 任务 2 · T12 · D2 教师端录制（70s）

### 脚本

`@F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\record-d2-teacher.mjs`

### 执行

```powershell
node .tmp/demo-video/record-d2-teacher.mjs
```

### 预期输出

```
.tmp/demo-video/out/d2/
├── teacher.webm   (~70s, 393×852)
├── events.json
└── frames/
```

### 镜头脚本（剧本 04 §2.4）

| 起-止 | 操作 |
|---|---|
| 0-10s | 工作台 hero + 4 数据卡 + 待处理列表（滚动）|
| 10-30s | 数据看板（4 卡 → 趋势 → 学院分布 → 时段热力 → AI 成本，滚动 3 次）|
| 30-50s | 知识库 → 高频待补卡 → 点『去补充』→ 详情 |
| 50-70s | profile 紫粉 hero + 系统设置滚动 |

### 视口约定

教师端 H5 是 mobile-first，**按 393×852 录制**（不是 desktop 1920×1080）。Remotion 后期放在 1920×1080 横屏舞台中央，左右留字效空间。

### selector 调试同 T11

特别关注：
- 底部 Tab『知识库』点击是否切走 — 如 switchTab 在 H5 不工作，改用 `text=知识库` 直接 click
- 『去补充』按钮 — 实际可能是 `.kb-card .action-btn` 或 `button:has-text("去补充")`

### 验收

- ☐ `out/d2/teacher.webm` 文件大小 > 3 MB
- ☐ events.json events 数量 > 10
- ☐ 视觉抽检：能看到 dashboard → analytics（含学院分布/热力图）→ 知识库 → profile

---

## 任务 3 · T13 · D3 双端实时分屏录制（50s ⭐）

**这是全片最炫的高潮。最难一段。**

### 前置自检

跑之前先确认 Centrifugo 推送链路通：

```powershell
# 跑 v7 e2e（应全 PASS）
node .tmp/demo-video/test-realtime-v7.mjs
```

如果 v7 失败，**不要跑 T13** —— 推送通道有问题，先告诉 Cascade。

### 脚本

`@F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\record-d3-dual.mjs`

### 执行

```powershell
node .tmp/demo-video/record-d3-dual.mjs
```

### 预期输出

```
.tmp/demo-video/out/d3/
├── student/
│   ├── student.webm        (~50s)
│   └── events.json
├── teacher/
│   ├── teacher.webm        (~50s)
│   └── events.json
└── sync.json               t0 锚点 + setup_duration_ms（Remotion 用来对齐）
```

### 关键机制

1. **双 context 并行录制**：脚本 newContext 两次，每个带 `recordVideo`，输出独立 webm
2. **t0 同步锚点**：`t0 = Date.now()`，两端 events.json 都基于 (Date.now() - t0)
3. **学生 setup 用 pendingConversationId**：参考已修复的脚本（line 156-164）
4. **关闭流程**：用 Promise.all 同时 close 两个 context，避免一端先关导致时长不一致

### 操作序列（脚本已写）

| 时间 | 学生侧 | 教师侧 |
|---|---|---|
| 0-2s | 已在『等待老师』静态页 | 已在工作台 |
| 2-10s | 静默 | 看待处理卡片 |
| 10-22s | 静默 | 点 detail → 接单 |
| 22-37s | **实时收到 3 条消息**（Centrifugo 推送）| 打字 + 发送 3 次 |
| 37-50s | API 发回复『谢谢老师』 | 标记已解决 |

### selector 调试要点

| 步骤 | 当前 selector | 调试方法 |
|---|---|---|
| 教师端 detail 卡片 | `[data-conv-id="..."], .conv-card` | 脚本已 fallback 用 goto URL |
| 教师端接单按钮 | `button:has-text("接单")` | 可能 conv 状态已 pending_teacher 不需要 accept |
| 教师端输入框 | `textarea, .reply-input textarea` | 教师 detail.vue 的 reply 区 |
| 教师端发送按钮 | `button:has-text("发送"), .send-btn` | 同上 |
| 教师端已解决按钮 | `button:has-text("已解决"), button:has-text("解决"), button:has-text("结束")` | 脚本已 fallback 用 API |

### 验收（最关键）

- ☐ `out/d3/student/student.webm` + `out/d3/teacher/teacher.webm` 双方都 > 2 MB
- ☐ `out/d3/sync.json` 含 `t0_epoch_ms` 和 `setup_duration_ms` 字段
- ☐ `out/d3/student/events.json` 中有 `type: "recv_msg"` × 3（学生端收到 3 条消息）
- ☐ `out/d3/teacher/events.json` 中有 `type: "send_msg"` × 3（教师端发了 3 条）
- ☐ 双方 events.json 中 send_msg → recv_msg 的延迟 `(recv.t_recv - send.t_sent)` 都 < 2000ms（实时推送有效）
- ☐ **视觉抽检学生 webm**：能看到 3 条消息自动跳出来（不需要学生 page 操作）
- ☐ **视觉抽检教师 webm**：能看到教师在打字 + 发送

---

## 完成后回报

按顺序跑：T11 → T12 → T13（每段都验证完才进下一段）。

完成后报告：

```
T11:  out/d1/student.webm 大小=??? MB, 时长=???s, events=??? 个
T12:  out/d2/teacher.webm 大小=??? MB, 时长=???s, events=??? 个
T13:  out/d3/student/student.webm + teacher/teacher.webm
       sync.json t0=???, setup_duration=???ms
       send-recv 延迟均值=???ms
```

如有 selector 调整，把改动 diff 告诉 Cascade。

---

## 不要做的事

- ❌ 不要 commit / push 录制产物（webm 大且不入库）
- ❌ 不要关 SSH tunnel `localhost:18000`
- ❌ 不要动 vite.config.ts 临时 proxy
- ❌ 不要改 services/gateway/ 后端代码
- ❌ T13 失败时不要硬跑 — 先确认 v7 e2e 通过
