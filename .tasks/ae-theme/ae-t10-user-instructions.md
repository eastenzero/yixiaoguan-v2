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

## 步骤 4 · 设 Work Area + 渲染（10-20 分钟）

4 个 SCENE 总共约 34 秒，没必要渲染整个 251s 主合成。

### 方法 A：分别渲染 4 段（推荐）

每个 SCENE 单独渲染，便于 Remotion 编排时灵活拼接。

1. 找到 SCENE_01 在时间轴的起止位置
2. 拖时间指针到起点，按 **B** 键设入点
3. 拖到结点，按 **N** 键设出点
4. 菜单 **Composition > Add to Render Queue**
5. Render Queue 面板：
   - Output Module: **H.264**（如没有这选项装 AME 或选 QuickTime + h264 codec）
   - Output To: `F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-scene-01.mp4`
6. 点 Render
7. SCENE_05 / 10 / 13 各重复 5-7 步

输出 4 个文件：
- `ae-scene-01.mp4`（8s）
- `ae-scene-05.mp4`（8s）
- `ae-scene-10.mp4`（10s）
- `ae-scene-13.mp4`（8s）

### 方法 B：一次性渲染整个 0-1:32 段

简单粗暴，渲整段一次性出来，Remotion 编排时再切。

1. B 键设入点 0:00
2. N 键设出点 1:32（覆盖到 SCENE_13 结束）
3. Render Queue → H.264 → `ae-segment-v2.mp4`
4. 点 Render

**预估渲染时间**：92 秒视频 × 4K 比 1080p 慢 4-5 倍。**建议先用 HD (1920×1080) 合成渲，不用 4K**。HD 渲约 5-10 min。

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
