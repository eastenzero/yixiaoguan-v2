# 副窗口任务 · T10 AE 字幕添加 + 4 段 mp4 渲染

> 2026-05-12 凌晨 主对话导演产出
> 目标交付物：4 段独立的 SCENE mp4 + 中文字幕，**带 AE 原生 3D 立体穿插效果**

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2
```

后续所有路径都以这个为根。

---

## 一句话目标

把 AE 模板里的 4 个 SCENE 合成（SCENE_01 / 05 / 10 / 13）：

1. 替换屏幕占位为医小管真截图
2. 加上中文字幕（**复用模板 Text Holder 拿到 3D 穿插效果**）
3. 各自独立渲染成 4 段 mp4

输出到：

```
F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scene-01.mp4   (SCENE_01, 8s,  单台手机, 学生 home)
F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scene-05.mp4   (SCENE_05, 8s,  单台手机, 学生 chat 流答)
F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scene-10.mp4   (SCENE_10, 10s, 双台手机, 学生 chat × 教师 dashboard)
F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scene-13.mp4   (SCENE_13, 8s,  双台手机, 学生 services × 教师 analytics)
```

如果 AE 输出不便给 mp4，**输出 .mov 也可以，最后用 ffmpeg 转 mp4**（我给你一段 ffmpeg 命令）。

---

## 上下文：模板与已知事实

### AE 模板
- **App Promo Phone 14 Pro Mockup Pack**（Videohive 40526693）
- 模板里 30 个 SCENE 合成（SCENE_01 ~ SCENE_30），每个都是独立 CompItem
- 之前已跑过 `ae-light-theme.jsx` 改成亮色主题（紫色机身 + 浅紫渐变背景 + 深紫 #5B21B6 文字色），**不要重跑**

### 4 个目标 SCENE 的真实结构（已 inspect 确认）
完整 inspect 数据：`@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scenes-real-structure.json`

| SCENE | 时长 | 屏幕数 | 背面手机层 | 文字层 | 状态 |
|---|---|---|---|---|---|
| SCENE_01 | 8.03s | 1 | 0 | **无** | 需加字幕 |
| SCENE_05 | 8.03s | 1 | 0 | **无** | 需加字幕 |
| SCENE_10 | 10.03s | 2 | 0 | **无** | 需加字幕 |
| SCENE_13 | 8.03s | 2 | 0 | **无** | 需加字幕 |

**关键**：4 个目标 SCENE **全部没有原生文字层**。模板里有 16 个 SCENE 用了 `Text Holder` 嵌套合成（SCENE_04 / 11 / 12 / 15 / 17-20 / 22 / 23-28 / 30），那才是模板设计师调好的"3D 文字穿插"组件。

### 屏幕替换映射
已写好的 jsx：`@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-replace-screens.jsx` —— 直接 `File > Scripts > Run Script File...` 跑即可。它会替换 6 个 placeholder：

| SCENE | Screen | 截图 |
|---|---|---|
| SCENE_01 | Screen 01 | `.tasks/student-ui-audit-2026-05-11/after-avatar/02-home.png` |
| SCENE_05 | Screen 01 | `.tasks/student-ui-audit-2026-05-11/after-avatar/04-chat-with-conv.png` |
| SCENE_10 | Screen 01 | `.tasks/student-ui-audit-2026-05-11/after-avatar/03-chat-empty.png` |
| SCENE_10 | Screen 02 | `.tasks/teacher-ui-audit-2026-05-11/after-avatar/02-dashboard.png` |
| SCENE_13 | Screen 01 | `.tasks/student-ui-audit-2026-05-11/after-avatar/06-services.png` |
| SCENE_13 | Screen 02 | `.tasks/teacher-ui-audit-2026-05-11/after-avatar/09-analytics.png` |

**SCENE_05 的 `04-chat-with-conv.png` 有 2 个瑕疵需要先修**（详见 Step 0）：
- ❌ tab bar 在画面中段又出现一次（fullPage 截图把 fixed positioned tab 重复抓了）
- ❌ 前两条对话气泡是 `[v7-r1-1778510893945] 老师 UI 实时回复 round 1` / `[v7-r2-...] 学生 UI 提问 round 2` —— 是 realtime e2e 测试遗留的脏 demo 数据
- ❌ 底部还有一条"拜拜"测试残留

### 中文字幕文案（最终稿）
来源：`@F:\Documents\code\yixiaoguan-v2\video\06-ae-text-final.md`

| SCENE | 字幕 | 字数 |
|---|---|---|
| SCENE_01 | 智能问答 · 秒答常见问题 | 10 |
| SCENE_05 | AI 流式回答 | 6 |
| SCENE_10 | 学生有问 · 老师在场 | 10 |
| SCENE_13 | 全场景洞察 | 6 |

字幕颜色 `#5B21B6` 深紫（已通过 ae-light-theme.jsx 在模板里统一改色），**字体需要换成支持中文的字体**（Lato Bold 不支持中文会显示方块）。

### Text Holder 复用思路
我已经写了一个**只读探测脚本**帮你看清 Text Holder 内部结构 + 系统里哪些中文字体可用：

```
@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-inspect-text-holder.jsx
```

跑它会 alert 出：
- SCENE_04 / 11 / 12 等 6 个候选 SCENE 里 Text Holder 的层情况
- Text Holder comp 内部所有图层（哪个是 TextLayer / 当前 font / size / color）
- 12 种中文字体在用户机器上的可用性（✓/✗ 列表）

跑完这个 inspect 你就有所有信息决定下一步怎么写"复制 Text Holder 到 4 个 target + 改文字 + 改字体"的脚本。

---

## 任务清单

按顺序做：

### 0. 先重截 `04-chat-with-conv.png`（必做，否则 SCENE_05 出来全是 v7 测试垃圾文字）

**现状**：当前的 `.tasks/student-ui-audit-2026-05-11/after-avatar/04-chat-with-conv.png` 有 3 处瑕疵（见上文 §屏幕替换映射）

**capture 脚本位置**：`@F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\student-audit-capture.mjs`

脚本逻辑（自己看）：
- API 登录学生 `4125150011/4125150011`
- 找一条已有的 conv 注入 `pendingConversationId` 跳进去 + `fullPage: true` 截图
- 当前 conv 选取逻辑没过滤 v7 脏数据，所以选到了一个含 `[v7-r1-...]` 测试消息的 conv

**修法二选一**（推荐前者）：

**方案 A：让脚本主动创建一条干净 demo conv**
- API 调 `POST /api/conversations` 新建 → 调 `POST /api/chat/send` 发一条干净提问（如"医保报销怎么办理？"）→ 等 AI 流式回答完成 → 用这条新 conv 截图
- 干净彻底，但需多走 2-3 个 API

**方案 B：过滤含 v7 / round / [v7- 标记的 conv**
- 拿现有 conv 列表 → filter 掉 title/last_message 含 `v7` / `round` / `拜拜` / `[` 的
- 选剩下最近的一条
- 简单但依赖现有数据库里有干净 conv

**且无论哪个方案，把 `fullPage: true` 改成 `fullPage: false`**（截单 viewport 即可，避免 tab bar 重复出现）。模板手机屏幕区域受限，截上半屏 1-2 条对话气泡 + composer 即可，tab bar 留在底部固定位置不滚动。

**服务器/账号**：
- gateway: 165 dev `http://192.168.100.165:8100`（或脚本里写好的）
- 学生 H5 dev: 跑 `apps/student-app` 的 `npm run dev:h5`（端口 3001）
- 学生账号: `4125150011/4125150011`

**验收**：新生成的 PNG 应该满足：
- ✓ tab bar 只出现在底部一次
- ✓ 画面里至少有 1 条干净的学生提问 + 1 条干净的 AI 回答
- ✓ 没有 `[v7-r` / `round` / `拜拜` 这些字符串
- ✓ 文件覆盖到原路径 `.tasks/student-ui-audit-2026-05-11/after-avatar/04-chat-with-conv.png`

**如果你尝试 30 分钟仍跑不通这步**：把当前进度（脚本改动 / 错误日志）留在 `.tmp/demo-video/out/` 下，回报主对话，跳过 Step 0 直接做 Step 1（接受瑕疵渲一版，主对话后续单独重渲 SCENE_05）。

### 1. 屏幕替换
跑 `ae-replace-screens.jsx`（路径见前文）→ 确认 alert 报告 6 项全 ✓。

### 2. 探测 Text Holder
跑 `ae-inspect-text-holder.jsx`，把 alert 报告**复制保留**（后面写脚本要用 + 终验收要用）。

### 3. 加中文字幕（核心）
- **机制**：复制 Text Holder 嵌套合成 4 份独立副本（每个 target SCENE 一份），改各自副本内部 TextLayer 的文字 + 字体
- **为什么是 duplicate**：直接把同一个 Text Holder 加到 4 个 SCENE 会导致改一个文字 4 处都变（comp 引用复用）
- **字体**：从 inspect 报告里挑一个中文可用的（推荐优先级：思源黑体 CN > 微软雅黑 > 阿里巴巴普惠体）
- **验收**：在 AE 时间轴跳到 SCENE_01/05/10/13 各预览一下，文字应该：
  - 中文正常显示（不是方块）
  - 颜色深紫（跟亮色背景对比清晰）
  - 跟手机有 3D 穿插立体感（手机移动时文字保持 3D 景深）
  - 入场/出场动画自然

写脚本时**关键 ExtendScript API**：
- `compItem.duplicate()` 复制整个嵌套合成
- `comp.layers.add(item)` 把 comp item 加为 layer
- `textLayer.property("Source Text")` 拿 SourceText 属性
- `prop.value` 是 TextDocument，改 `.text` 和 `.font` 后必须 `prop.setValue(td)` 写回

### 4. 渲染 4 段 mp4

⚠️ **不要渲主合成的 Work Area**！

模板主合成 `PREVIEW COMPS`（251s 长）里 SCENE_01 → SCENE_13 之间穿插了 SCENE_02 / 03 / 07 / 11 / 12 这种**带苹果 logo 的背面手机过场**。如果按时间轴 Work Area 渲，logo 会出现在最终视频里。

**正确做法**：在 Project Panel 里**双击打开** SCENE_01 / 05 / 10 / 13 让其成为 active comp，分别 Composition > Add to Render Queue，独立各渲一段。

输出格式建议：H.264 mp4（如果 AE 装了 Media Encoder）；fallback 用 QuickTime / Lossless mov，最后 ffmpeg 转 mp4：

```bash
# 在 .tasks/ae-theme/ 目录下
ffmpeg -i ae-scene-01.mov -c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow ae-scene-01.mp4
# 4 段都跑一遍
```

输出尺寸保持模板原始（应该是 3840×2160 或 1920×1080，看 SCENE 合成的 width/height），不要降级。

---

## 约束

- **不要碰 git**（add / commit / push 都不要做，主对话统一管 git）
- **不要修改其他文件**（除了往 `.tasks/ae-theme/` 写新 jsx 脚本和最终 mp4 输出）
- **不要碰 SCENE_13 的渲染选择问题** —— 4 段都要，主对话已确认
- **不要试图修复 chat 截图断层** —— 这个瑕疵后期单独处理，本次任务接受瑕疵
- **不要触发 ae-light-theme.jsx**，已经跑过了重跑会乱
- 中间产物（jsx 草稿、字体测试、AE 工程文件改动）都可以本地保留，不要清理

---

## 卡壳怎么办

如果遇到下列任一情况就**停下来回报主对话**（不要硬上）：

- inspect 报告里所有候选字体都 ✗（中文字体全没装）
- duplicate Text Holder 后改文字总是失败 / 4 个 SCENE 文字串扰
- 字幕加完后预览发现没有 3D 穿插效果（变成平面贴字）
- Render Queue 里找不到 H.264 输出选项也没装 Media Encoder
- 任何 ExtendScript 报错卡 30 分钟以上

回报时把以下信息一起发回主对话：
1. 你跑了哪些脚本 / MCP 调用
2. alert 弹窗的截图或文字内容
3. 当前 AE 工程文件状态（4 个 SCENE 哪些已替换、哪些已加字、哪些已渲）

---

## 终验收清单

主对话验收时会看：

- [ ] 4 段 mp4 文件都存在且 > 1 MB
- [ ] 时长分别是 8s / 8s / 10s / 8s（可以 ±0.1s）
- [ ] 视频尺寸 1920×1080 或 3840×2160（不要 1080×1920 这种竖屏）
- [ ] 单台手机 SCENE（01 / 05）画面里没有出现第二台手机
- [ ] 双台手机 SCENE（10 / 13）画面里两台手机都正面无 logo
- [ ] 4 段都有中文字幕，文字内容跟上面文案表一致
- [ ] 字幕中文正常显示（不是方块 / 乱码）
- [ ] 字幕跟手机 mockup 有立体穿插或景深感（不是平面贴字）
- [ ] 整体亮色主题保持（浅紫渐变背景 + 紫色机身 + 深紫文字）

跑完了把 4 段 mp4 路径 + 关键截图（每段视频中段抽 1 帧）回报主对话。
