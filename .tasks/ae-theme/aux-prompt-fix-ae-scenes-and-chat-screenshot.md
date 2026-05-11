# 副窗口派单 · AE SCENE 真实结构探查 + 学生 chat 截图断层修复

> 2026-05-12 凌晨 主对话 Cascade 产出
> 派给副窗口 AI（kimi / opencode / 另一个 Cascade 会话）独立接手这两件事，主对话保持上下文干净。
> 完成后只回报"哪几个 SCENE 改成什么"+"新截图路径"即可，主对话立刻继续推进。

---

## 你接手的两件事

### Bug A · AE 双 iPhone 镜头一正一反带 logo（剧本不符）

**现象**（用户原话）：preview-light-v2.mp4 里出现"双 iPhone 一正一反，背面那台带苹果 logo"。

**根因**：`@F:\Documents\code\yixiaoguan-v2\video\03-ae-template-analysis.md` 把双屏 SCENE 简单归到"17 个无 logo"列表，但实际上模板里某些"双屏 SCENE"是**一台正面 + 一台背面**展示，背面那台机身上有苹果风 logo 烘焙在 .mov 中**无法移除**。

**叙事要求**（剧本 04 §2.2）：AE 段需要双屏镜头展示"学生端 × 教师端"两台正面 — **两台都要正面、都要能塞屏幕内容**。

**当前可疑 SCENE**（按当前 `ae-replace-screens.jsx` 选择）：
- SCENE_10（10s 双屏）— 怀疑一台是背面
- SCENE_13（8s 双屏）— 同样怀疑

**任务**：探查 17 个候选 SCENE 真实情况，找 2 个真正"两台正面 + 都有 Screen 01/02 占位"的 SCENE，替换 SCENE_10 + SCENE_13。

### Bug B · 学生 chat 截图断层

**现象**：`.tasks/student-ui-audit-2026-05-11/after-avatar/04-chat-with-conv.png` 太长，tab bar 在中间出现一次后下面又接消息内容。

**根因**：`student-audit-capture.mjs` 用 `fullPage: true`，message list 内容超过 viewport 高度，position: fixed 的 tab bar 在 viewport 高度位置渲染了一次，下面是被 tab bar 遮住的消息内容。

**影响**：AE 段 SCENE_05（学生 chat 流答）用这张图作为 iPhone 屏占位会很难看。

**任务**：重截一张 viewport-only (`fullPage: false`) 的版本，或滚到合适位置截。

---

## 你需要读的上下文

按顺序读这 5 个文件（都已 commit）：

| # | 文件 | 用途 |
|---|---|---|
| 1 | `@F:\Documents\code\yixiaoguan-v2\video\04-script-plan.md` | 剧本契约，§2.2 AE 段决策 |
| 2 | `@F:\Documents\code\yixiaoguan-v2\video\03-ae-template-analysis.md` | 17 个候选 SCENE 列表（注意此文件可能误判，要核实） |
| 3 | `@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-light-theme-report.md` | 之前的亮色改造报告 |
| 4 | `@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-replace-screens.jsx` | 当前替换脚本（要改） |
| 5 | `@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\scene-mapping.md` | SCENE 映射表（要改） |

还有现成工具：
- `@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-inspect.jsx` — dump AE 项目结构到 JSON（用户在 AE 里跑）
- `@F:\Documents\code\yixiaoguan-v2\.tasks\student-ui-audit-2026-05-11\after-avatar\` — 学生端 7 张截图
- `@F:\Documents\code\yixiaoguan-v2\.tasks\teacher-ui-audit-2026-05-11\after-avatar\` — 教师端 11 张截图

---

## 工作流（Bug A）

### Step 1 · 写一个新 inspect 脚本

写 `@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-inspect-double-screen-scenes.jsx`，对所有 `SCENE_XX` 合成做下面的检查：

```js
// 伪代码
for each SCENE comp:
    layers_with_screen_keyword = layers whose name contains "Screen"
    has_phone_back = layers whose name contains "back" or has "logo" footage source
    output: { scene_name, num_screen_layers, has_back_phone, enabled_phone_color_layers }
```

输出 JSON 到 `.tasks/ae-theme/ae-scenes-real-structure.json`，包含每个 SCENE 的真实信息。

### Step 2 · 用户在 AE 里跑你的 inspect 脚本

让用户：
1. AE > File > Scripts > Run Script File... > 选你的 ae-inspect-double-screen-scenes.jsx
2. 把生成的 `ae-scenes-real-structure.json` 发给你

### Step 3 · 根据 JSON 找 4 个理想 SCENE

筛选标准（按优先级）：
1. ✅ 必要：所有"屏幕占位"图层数 ≥ 2（双屏 SCENE）
2. ✅ 必要：所有手机层都是"正面"展示（不能有 back/logo 痕迹）
3. ✅ 必要：时长 8-10s
4. ⭐ 加分：亮色背景下视觉评分高（参考 ae-light-theme-report.md Part B）

候选范围：03 文档列的 17 个 SCENE 全部重新评估 — 不要再相信"17 个无 logo"标签。

### Step 4 · 更新 ae-replace-screens.jsx 和 scene-mapping.md

把新选定的 4 个 SCENE 写入 `REPLACEMENTS` 数组，更新映射表。如果新 SCENE 时长跟原来的不一样（例如原来 SCENE_10 是 10s，新换的是 8s），告诉主对话 Cascade 调整剧本时间轴。

### Step 5 · 用户重新跑 ae-replace-screens.jsx 验证

确认 alert 里 ✓ 全部、SCENE 内图层无 logo 痕迹、预览双屏镜头是"两台正面"。

---

## 工作流（Bug B）

### Step 1 · 看现有截图判断断层位置

打开 `.tasks/student-ui-audit-2026-05-11/after-avatar/04-chat-with-conv.png`，确认 tab bar 出现位置。

### Step 2 · 抄改 student-audit-capture.mjs

改一个新 route，输出 viewport-only PNG。建议：

```js
// 新增 route: 04a-chat-streaming（viewport-only，无 tab bar 重复）
{
  name: "04a-chat-streaming",
  path: "/#/pages/chat/index",
  wait: 3500,
  preStorage: { pendingConversationId: String(demoConvId) },
  fullPage: false,  // ← 关键
},
```

让 screenshot 调用支持 `fullPage` 参数（默认 true）。

### Step 3 · 跑脚本生成新截图

```powershell
node .tmp/demo-video/student-audit-capture.mjs after-avatar
```

新增 `.tasks/student-ui-audit-2026-05-11/after-avatar/04a-chat-streaming.png`（393×852 viewport-only）。

### Step 4 · 更新 ae-replace-screens.jsx

把 `REPLACEMENTS` 里 SCENE_05 的 image 从 `04-chat-with-conv.png` 改为新的 `04a-chat-streaming.png`。

---

## 给副窗口 AI 的关键约束

- 🚫 **不要 commit / push**（主对话 Cascade 统一管 git）
- 🚫 **不要改 services/gateway/ 后端代码**
- 🚫 **不要动 SSH tunnel localhost:18000**
- 🚫 **不要碰 D1/D2/D3 录制脚本**（主对话和 Kimi 在并行用，避免冲突）
- ✅ **只改 4 个文件**：
  - `.tasks/ae-theme/ae-inspect-double-screen-scenes.jsx`（新增）
  - `.tasks/ae-theme/ae-scenes-real-structure.json`（新增，AE 跑出来）
  - `.tasks/ae-theme/ae-replace-screens.jsx`（修改 REPLACEMENTS）
  - `.tasks/ae-theme/scene-mapping.md`（更新映射表）
  - `.tmp/demo-video/student-audit-capture.mjs`（增加 viewport-only 截图）
  - `.tasks/student-ui-audit-2026-05-11/after-avatar/04a-chat-streaming.png`（新截图）

---

## 完成后回报

回报给主对话 Cascade（用户转述即可），包含：

```
Bug A:
  原选: SCENE_10 + SCENE_13
  新选: SCENE_X + SCENE_Y（理由: ...）
  时长变化: 原 10+8=18s → 新 ???+???=???s
  ae-replace-screens.jsx 已更新

Bug B:
  新截图: .tasks/student-ui-audit-2026-05-11/after-avatar/04a-chat-streaming.png（??? KB）
  ae-replace-screens.jsx SCENE_05 已切换到新截图
```

主对话 Cascade 拿到这两个信息后：
- 如果新 SCENE 总时长有变 → 调整 04-script-plan.md 时间轴
- 拿新版 ae-replace-screens.jsx 给用户跑 + 渲染 HD
- 进 T14 Remotion 总编排
