# T10 用户操作指南 · AE 重渲

> 2026-05-11 23:50 导演产出
> 这是给你（用户）在 AE 里**手动操作**的 5 步流程。Cascade 已就绪屏幕替换脚本，但 AE MCP bridge 不稳定，需要你点几下鼠标。
>
> 配套脚本：`@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-replace-screens.jsx`
> 配套映射：`@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\scene-mapping.md`

---

## 前置确认

跑脚本之前先确认 4 件事：

| 项 | 验证 |
|---|---|
| **学生端截图就绪** | `.tasks/student-ui-audit-2026-05-11/after-avatar/` 应有 7 张 PNG（Kimi 已跑） |
| **教师端截图就绪** | `.tasks/teacher-ui-audit-2026-05-11/after-avatar/` 应有 11 张 PNG |
| **AE 模板已打开** | `Phone 14 Pro_App Presentation_CS6.aep`（百度网盘下载位置） |
| **亮色主题已应用** | 之前已经跑过 `ae-light-theme.jsx`，preview-light-v2.mp4 是亮色版本 |

如果还没跑亮色主题，先跑 `ae-light-theme.jsx`（File > Scripts > Run Script File...）。

---

## 步骤 1 · 跑屏幕替换脚本（30 秒）

1. AE 里打开 `Phone 14 Pro_App Presentation_CS6.aep`
2. 菜单 **File > Scripts > Run Script File...**
3. 选 `F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-replace-screens.jsx`
4. 等 alert 弹窗

## 步骤 2 · 看 alert 报告（关键验收点）

alert 会显示两块内容：

### A. 替换结果

```
✓ 学生 home               [SCENE_01 > Screen 01] ← 02-home.png
✓ 学生 chat 流答           [SCENE_05 > Screen 01] ← 04-chat-with-conv.png
✓ SCENE_10 左·学生 chat   [SCENE_10 > Screen 01] ← 03-chat-empty.png
✓ SCENE_10 右·教师 dashboard  [SCENE_10 > Screen 02] ← 02-dashboard.png
✓ SCENE_13 左·学生 services [SCENE_13 > Screen 01] ← 06-services.png
✓ SCENE_13 右·教师 analytics [SCENE_13 > Screen 02] ← 09-analytics.png
```

**期望**：6 项全部 ✓。如果有 ✗，告诉 Cascade 错误信息，调整脚本。

**常见错误**：
- `screen layer not found: Screen 02 in SCENE_10` — 模板里双屏 SCENE 的第二台手机可能不叫 "Screen 02"。看下面"图层结构 dump"找实际层名
- `file not found: ...` — 截图路径不对或 Kimi 截图还没完

### B. 4 SCENE 图层结构 dump（排查 Bug 2 logo）

```
── SCENE_01 图层结构 ──
   #1 P01/P02 Controller [comp] xxx
   #2 Camera [...]
   #3 Screen 01 [footage] 02-home.png   ← 刚替换
   #4 Purple [...]
  ✗ #5 Blue [...]    ← disabled OK
  ✗ #6 Black [...]
   ...
```

**找 logo 残留**：在每个 SCENE 的图层结构里找下面字眼的层，如果是 `enabled = ✓`，可能就是 Bug 2：

- `logo` / `apple` / `brand` / `icon`
- `notch` 这种刘海层
- 任何 enabled = ✓ 但你不认识的 `[footage] ...` 层

找到后**记下 SCENE + 层名**，告诉 Cascade，我加到 disable 列表二次跑脚本。

---

## 步骤 3 · 时间轴预览（2 分钟）

打开主合成 **PREVIEW COMPS** (3840×2160) — 模板里那个 251s 长的总合成。

依次跳到这 4 个时间点（B 键设入点 / N 键设出点 / 空格预览）：

| SCENE | 时间锚点（估算） | 预期看到 |
|---|---|---|
| SCENE_01 | ~0:00-0:08 | 单台紫色 iPhone 慢推 → 屏幕是医小管 home 紫粉 hero + 16 项服务 |
| SCENE_05 | ~0:32-0:40 | iPhone 旋入 → 屏幕是 chat 双向气泡（紫色学生 + 绿色老师） |
| SCENE_10 | ~1:06-1:16 | **双屏对比**：左台 iPhone 学生 chat，右台 iPhone 教师 dashboard |
| SCENE_13 | ~1:24-1:32 | **双屏对比**：左台学生 services 格子墙，右台教师 analytics 数据看板 |

**关键验证点（针对 Bug 1）**：SCENE_10 和 SCENE_13 必须看到**两台手机并列**。如果只看到一台，说明这次替换没修复 Bug 1，告诉我。

**关键验证点（针对 Bug 2）**：每个 SCENE 都看不到苹果 logo / brand 图标。如果还有，回到步骤 2 看图层 dump 找出层名。

---

## 步骤 4 · 独立渲染 4 个 SCENE 合成（10-15 分钟）

> ⚠️ **关键警告**：**不要**用主合成 (PREVIEW COMPS) 的 Work Area 一次性渲 0-1:32！
>
> 主合成里 SCENE_01 → SCENE_13 之间穿插着 **SCENE_02 / SCENE_03 / SCENE_07 / SCENE_11 / SCENE_12** 这 5 个**背面/双背面**SCENE — 它们的手机机身上烘焙了苹果 logo，无法移除。这就是 preview-light-v2.mp4 里看到"一正一反带 logo"的真正原因。
>
> 正确做法：**直接打开 4 个 SCENE 合成本身，分别渲染**，跳过中间所有过场。

### 4 个 SCENE 的真实参数（来自 ae-scenes-real-structure.json）

| SCENE 合成名 | 时长 | 屏幕数 | Phone Back | 角色 |
|---|---|---|---|---|
| `SCENE_01` | 8.03s | 1 | 0（纯正面）| 学生 home 单屏 |
| `SCENE_05` | 8.03s | 1 | 0（纯正面）| 学生 chat 流答单屏 |
| `SCENE_10` | 10.03s | 2 | 0（双正面）| 学生 chat × 教师 dashboard |
| `SCENE_13` | 8.03s | 2 | 0（双正面）| 学生 services × 教师 analytics |

**AE 段总时长 = 8 + 8 + 10 + 8 = 34s**（剧本 04 写 30s，差 4s，T14 编排时给 D1 让 4s 即可，不必动 AE 段）

### 渲染步骤（4 个 SCENE 各跑一遍）

对 `SCENE_01` / `SCENE_05` / `SCENE_10` / `SCENE_13` 每个合成：

1. **Project 面板找到合成**：在 Project Panel 里搜 `SCENE_01`（双击打开），它是一个独立 Composition（不是主合成里的图层）
2. **设为当前合成**：双击使它成为时间轴的当前合成
3. **菜单**：Composition > Add to Render Queue
4. **Render Queue 面板**：
   - **Render Settings**: Best Settings / Full Resolution（如果电脑配置不行可以选 Half）
   - **Output Module**: H.264 (如没有这选项装 AME 或选 QuickTime + h264 codec)
   - **Output To**: `F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scene-01.mp4`
5. 点 **Render** 按钮
6. 等 1-3 分钟（每个 SCENE）

### 4 段输出

```
F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\
├── ae-scene-01.mp4   (8s)
├── ae-scene-05.mp4   (8s)
├── ae-scene-10.mp4   (10s)
└── ae-scene-13.mp4   (8s)
```

**预估总渲染时间**：4 段各 1-3 min · HD 1920×1080 输出约 10-15 min。如果嫌慢，先用 1080p 渲（不用 4K），Remotion 编排时一致即可。

### 为什么不一次性渲

如果用主合成 Work Area 0-1:32，会包含：
- ✅ SCENE_01 (0:00-0:08) — 学生 home 单屏
- ❌ SCENE_02 (0:08-0:16) — **背面 SCENE，logo 出现**
- ❌ SCENE_03 (0:16-0:24) — **双背面 SCENE，2 个 logo**
- ✅ SCENE_04 (0:24-0:32) — 单屏正面（但叙事没用）
- ✅ SCENE_05 (0:32-0:40) — 学生 chat 流答
- ❌ SCENE_06/07/...（中间还有背面 SCENE）
- ✅ SCENE_10 (1:06-1:16) — 双正面
- ❌ SCENE_11/12（背面 SCENE）
- ✅ SCENE_13 (1:24-1:32) — 双正面

中间那些 ❌ 是用户看到 logo 的来源，**必须跳过**。

---

## 步骤 5 · 验收

把渲完的 mp4 路径告诉 Cascade，我看一下：

- ☐ SCENE_01: 学生 home 真截图清晰展示
- ☐ SCENE_05: chat 流答画面 + 双向气泡
- ☐ SCENE_10: **双手机** 学生 × 教师 dashboard 并列
- ☐ SCENE_13: **双手机** 学生 services × 教师 analytics 并列
- ☐ 4 段都无 logo 残留
- ☐ 亮色背景（浅紫渐变白）保持

通过后这一段 AE 素材就**永久定稿**，进 Remotion 总编排（T14）。

---

## 如有问题

把 alert 弹窗截图 / 渲染产物截图发给 Cascade，我立刻调脚本或映射表。**不要在 AE 里手动替换图层**，那样会脱离脚本管理，下次重渲又得重做。
