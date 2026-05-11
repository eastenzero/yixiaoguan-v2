# SCENE 替换映射表（T10 工件）

> 2026-05-11 23:50 导演产出
> 配套脚本：`@F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\ae-replace-screens.jsx`

---

## 4 个 SCENE × 6 个屏幕占位

| # | SCENE | 时长 | 屏幕 | 替换为 | 来源 |
|---|---|---|---|---|---|
| 1 | SCENE_01 | 8s | Screen 01 | 学生端 home 首屏 | `.tasks/student-ui-audit-2026-05-11/after-avatar/02-home.png` |
| 2 | SCENE_05 | 8s | Screen 01 | 学生端 chat 流答 | `.tasks/student-ui-audit-2026-05-11/after-avatar/04-chat-with-conv.png` |
| 3 | SCENE_10 | 10s | Screen 01（左） | 学生端 chat 列表 | `.tasks/student-ui-audit-2026-05-11/after-avatar/03-chat-empty.png` |
| 4 | SCENE_10 | 10s | Screen 02（右） | 教师端 dashboard | `.tasks/teacher-ui-audit-2026-05-11/after-avatar/02-dashboard.png` |
| 5 | SCENE_13 | 8s | Screen 01（左） | 学生端 services | `.tasks/student-ui-audit-2026-05-11/after-avatar/06-services.png` |
| 6 | SCENE_13 | 8s | Screen 02（右） | 教师端 analytics | `.tasks/teacher-ui-audit-2026-05-11/after-avatar/09-analytics.png` |

**合计 34s**（与剧本 04 §2.2 一致）。

---

## SCENE 选择回顾

剧本 04 决定保持 v3 原选：**SCENE_01 / 05 / 10 / 13**（不替换 SCENE_10 为 SCENE_09）。

理由：用户明确要求"双视角并行"叙事，**双屏对比镜头不可省**。Bug 1（preview 双屏镜头缺失）就是因为 AE 报告 Part B 推荐替换为 SCENE_09 但用户期待双屏——本次替换回到 SCENE_10。

亮色背景下 SCENE_10 双屏对比稍弱（评分 7/10），通过下列方式补偿：
- 替换为真截图后，紫色 UI 的学生端 + 紫色 hero 的教师端**对比度增强**
- 阴影层不动（已经够强）
- 如预览后仍觉得双屏融在一起，再单独写 `ae-boost-shadows.jsx` 微调

---

## Bug 排查路径

### Bug 1：双屏镜头缺失

**根因**：AE 报告 Part B 推荐 SCENE_09 替换 SCENE_10，可能上一版预览跑了 SCENE_09 → 自然没双屏。

**本次修复**：脚本明确替换 SCENE_10 + SCENE_13 的双屏占位。预览时应看到这两个镜头。

### Bug 2：某个 SCENE 仍出现手机 logo

**排查方法**：本脚本运行后 alert 会 dump 4 个 SCENE 的所有图层名 + enabled 状态。读出来后能看到：

```
── SCENE_01 图层结构 ──
   #1 P01/P02 Controller [comp] xxx
   #2 Camera ...
   #3 Screen 01 ...
   #4 Purple ...
  ✗ #5 Blue ...     ← disabled
  ✗ #6 Black ...
  ...
   #N (?)brand_logo? [footage] xxx   ← 如果有 logo，应该在这种层
```

**疑点层**：
- 任何名字含 `logo` / `apple` / `brand` / `icon` / `notch` 的图层
- enabled = true 但 source 是 footage 且不在 5 色机身系列里

发现后告诉我层名，我加到 `disable_layers` 列表里二次跑脚本即可。

---

## 字幕（AE Text Holder 内容）

参考 `@F:\Documents\code\yixiaoguan-v2\video\06-ae-text-final.md` — T3 工件。

本脚本**不改文字**，文字层单独走 `ae-replace-texts.jsx`（等截图替换验收通过后再做）。

---

## 操作步骤

1. **前置**：先确认 Kimi 已完成 T8b 学生端截图（`.tasks/student-ui-audit-2026-05-11/after-avatar/` 7 张 PNG）
2. 打开 AE，加载模板 .aep 文件
3. （如未跑过）先跑 `ae-light-theme.jsx` 应用亮色主题
4. 跑 `ae-replace-screens.jsx`
5. 查看 alert 弹窗：
   - 替换是否全部 ✓
   - 4 个 SCENE 的图层结构
6. **预览**：在时间轴跳到 SCENE_01 / 05 / 10 / 13 各拉一下播放头，看屏幕内容
7. 如有 logo 残留，告诉 Cascade 哪个图层
8. 预览 OK 后渲染 HD 合成（Work Area 覆盖 4 SCENE 时间段）

---

## SCENE 时间锚点（30 个 SCENE 顺排估算）

| SCENE | 起始 | 结束 |
|---|---|---|
| SCENE_01 | ~0:00 | ~0:08 |
| SCENE_05 | ~0:32 | ~0:40 |
| SCENE_10 | ~1:06 | ~1:16 |
| SCENE_13 | ~1:24 | ~1:32 |

⚠️ 实际时间需打开 AE 在时间轴上确认（每个 SCENE 实际位置可能与估算偏差 ±2s）。
