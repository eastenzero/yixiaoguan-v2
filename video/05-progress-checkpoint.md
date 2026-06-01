# 05 · 视频项目阶段性 Checkpoint

> 截止 **2026-05-11 21:55** · 由 Cascade 导演线产出
> 接手的 AI 读这一份就够。完整剧本契约见 `video/04-script-plan.md`。

---

## 🎯 一句话现状

4-5 分钟产品演示长片的**导演盘子已敲定 + AE 亮色主题改造完成 + stock 片头 23 个候选已搜集**。
**UI 优化（用户单独对话）即将收尾**（最后在加模拟头像）。
**现在可以正式启动 Phase 1 录制流水线。**

---

## ✅ 已完成（不要重做）

### 1. 剧本契约 v3.1（亮色主题修订）
**文件**：`video/04-script-plan.md`（v3 在 commit `953511c`，v3.1 修订未 commit 在工作区）

关键决策：
- 4-5 分钟产品演示长片
- 结构：intro 8s + AE 30s + D1 学生 70s + D2 教师 70s + **D3 双端分屏 50s ⭐** + outro 10s
- 输出：**1920×1080 30fps H.264 横屏**
- 录制环境：内网 165 dev（实时推送已 e2e PASS）
- **整体亮色主题**（v3.1 修订，不是深色）
- 主色 `#7C3AED` 紫；AE 段背景 `#F5F3FF→#FFFFFF` 渐变；机身 Purple；文字 `#5B21B6`

### 2. AE 亮色主题改造 — 已渲预览
**目录**：`.tasks/ae-theme/`

| 文件 | 说明 |
|---|---|
| `ae-light-theme.jsx` | 改造脚本，`File > Scripts > Run Script File...` 一键执行 |
| `ae-light-theme-report.md` | Part A 改造摘要 + Part B 17 个 SCENE 亮色评估 |
| `preview-light-v2.mp4` | **60 MB 预览视频**（用户已看过，反馈见下方 🐞） |
| `ae-light-theme-manual-steps.md` | 备用手动操作指南 |
| 其他 jsx | bg-boost / inspect / fix / render-preview / render-quick |

### 3. Stock 片头候选 — 已搜集 + 评分
**目录**：`.tmp/demo-video/intro-candidates/`（23 个 mp4 + 缩略图 PNG）
**排名**：`.tmp/demo-video/intro-ranked.json`（99 候选 → 63 通过）

**Top 5（评分降序）**：
| # | 文件 | 时长 | 分辨率/fps | 评分 |
|---|---|---|---|---|
| 1 | `01-pexels-dynamic-abstract-purple-glowing-network--35062982.mp4` | 10s | 1920×1080@30 | **159** |
| 2 | `02-pexels-a-mesmerizing-animation-of-glowing-purpl-35390431.mp4` | 10s | 1920×1080@30 | 139 |
| 3 | `03-pexels-a-mesmerizing-display-of-abstract-glowin-35286322.mp4` | 10s | 1920×1080@30 | 139 |
| 4 | `04-pexels-dynamic-abstract-background-featuring-a--34549843.mp4` | 10s | 1920×1080@30 | 139 |
| 5 | `05-pexels-mesmerizing-wave-of-glowing-particles-in-34567729.mp4` | 10s | 1920×1080@30 | 139 |

均为 Pexels 紫色粒子/网络风，免费商用。

### 4. 实时推送链路修复（前置基础）— 已完成
- commit `8d4f587` on `fix/realtime-user-channel-push`
- v7 双端 UI e2e 全 PASS
- D3 双端分屏录制可放心走 165 dev 环境
- 复盘：`.tasks/realtime-fix-postmortem-20260511.md`

### 5. PoC 流水线 — 已验证
- `.tmp/demo-video/` 完整 Playwright + Remotion 工程
- `final-v1.mp4` 22s 学生端 demo 已渲出（1080×1920 流水线证明可行）
- ⚠️ 横屏 1920×1080 新工程需要重建 composition（旧 PoC 是竖屏）

---

## 🚧 进行中（用户单独对话推进）

**UI 优化** — 学生端 + 教师端演示路径 6+6 页面 polish。
**当前状态**：用户已报"修复完成"，**正在加模拟头像**（chat / history / profile / detail）。
**预计**：2-4 小时收尾，完成后用户回主对话报信号 "UI 完成"。

---

## 🐞 用户反馈的 Bug（待修，非阻塞 Phase 1 启动）

### Bug 1：AE preview 缺双手机并列镜头
**现象**：用户看 `preview-light-v2.mp4` 时**没看到** SCENE_10 / SCENE_13 的双屏对比镜头。
**原计划**：剧本里 SCENE_10（10s 双屏）+ SCENE_13（8s 双屏）应该展示"学生端 × 教师端并列"叙事。
**排查方向**：
1. AE 渲染的 Work Area 是否覆盖了 SCENE_10 (~1:06-1:16) 和 SCENE_13 (~1:24-1:32) 时间段？
2. 改造脚本是否意外把双屏 SCENE 的某层禁用了（比如启用 Purple 时把第二台手机的图层关了）？
3. 报告 Part B 里推荐用 SCENE_09（10s 单屏）替换 SCENE_10，那边 AI 是不是直接替换了导致用户期待的双屏没出现？

### Bug 2：某个 SCENE 仍出现手机 logo 图标
**现象**：用户在 preview 里某个场景看到手机 logo 图标。
**原计划**：03 文档已筛 17 个无 logo SCENE（01/04/05/06/08/09/10/13/15/23-30），可能漏了一个。
**排查方向**：
1. 用户选定的 4 个 SCENE 里哪个有 logo？01 / 05 / 10 / 13 全部 inspect 一遍
2. 是否是 Text Holder 区域有 brand icon 没改？

> 用户原话："这个你稍微记一下就行" — **优先级 P2**，不阻塞，UI 头像收尾后再处理。

---

## 📋 用户待决策项（不阻塞 Phase 1 启动）

| 项 | 选项 | 当前默认 |
|---|---|---|
| Stock intro 最终选哪个 | Top 5 任选 | 待用户挑（看缩略图后定） |
| SCENE_10 是否替换为 SCENE_09 | 替换 / 保持 | Cascade 推荐替换；用户反馈"想看双屏"，**默认保持 SCENE_10** |
| AE preview 两个 bug 立刻修 vs 等截图重渲一并修 | 立刻 / 等 | **建议等 T10 重渲时一并修**（节省一轮渲染） |

---

## 🚀 现在可以正式启动 Phase 1

按 `video/04-script-plan.md` §5 任务矩阵推进。

### 路线 A：UI 已完成（含头像）→ 立即起 6 件事

| 任务 | 派单 | 工时 |
|---|---|---|
| T8 截图（学生 + 教师端 polished UI 全页） | **Kimi CLI** | 4h |
| T9 测试数据填充（anjing 工单 + 学生提问） | Codex / Cascade | 2h |
| T10 AE 重渲（含真实 UI 截图，顺手修 Bug 1+2） | **Cascade + AE MCP** | 4h |
| T11 D1 学生端 demo 录制（Playwright 393×852） | **Kimi CLI** | 4h |
| T12 D2 教师端 demo 录制（Playwright 1920×1080 desktop） | **Kimi CLI** | 4h |
| T13 D3 双端实时分屏（Playwright 双 page t0 同步） | **Cascade + Kimi** | 6h |

### 路线 B：UI 还没完成 → 先做零依赖工件

| 任务 | 派单 | 工时 |
|---|---|---|
| T2 配音文案大纲（4-5 分钟分段中文旁白） | Cascade | 60min |
| T3 AE 段每屏短文字定稿（4 个 SCENE 各 8-12 字） | Cascade | 30min |
| T4 配音 API A/B 试听（ElevenLabs / Azure / 阿里云 / 火山） | Cascade + 用户 | 90min |
| T5 AE .jsx 屏幕替换脚本骨架 | Cascade | 90min |
| T6 D3 双 page Playwright 框架代码 | Cascade | 60min |

### 收口阶段

- **T14 Remotion 总编排**（intro + AE + D1 + D2 + D3 + outro + 字幕 + 配音 + BGM） → **opencode**（审美强）
- **T15 QA + 终片渲染** → Cascade + 用户

**预计**：UI 完成后 4-5 天出 v1 final.mp4。

---

## 🔗 关键路径速查

| 类型 | 路径 |
|---|---|
| **剧本契约 v3.1** | `video/04-script-plan.md` |
| 技术可行性 | `video/01-tech-feasibility.md` |
| 教师端页面清单 | `video/02-pages-inventory.md` |
| AE 模板分析 | `video/03-ae-template-analysis.md` |
| 本 checkpoint | `video/05-progress-checkpoint.md` |
| AE 亮色改造 | `.tasks/ae-theme/` |
| AE preview mp4 | `.tasks/ae-theme/preview-light-v2.mp4` |
| Stock 候选 | `.tmp/demo-video/intro-candidates/` |
| Stock 排名 | `.tmp/demo-video/intro-ranked.json` |
| PoC 工程 | `.tmp/demo-video/` |
| 实时推送复盘 | `.tasks/realtime-fix-postmortem-20260511.md` |

---

## 派单偏好（已确认）

- T8/T11/T12 截图 + 录制 → **Kimi CLI**
- T9 测试数据 → Codex 或 Cascade
- T10 AE 渲染 → **Cascade + AE MCP** + 用户验证
- T14 Remotion 编排 → **opencode**（审美强）
- T15 QA → Cascade + 用户

---

## 📢 给接手 AI 的话

你现在接手了一个已经在主仓里推进了 6+ 小时的视频项目。**剧本契约 v3.1 已落地、AE 改造完成、stock 候选搜集完成、实时推送修复完成**。

用户期待你：
1. **不要重新讨论方向、不要重复决策、不要再写新规划文档**
2. 立即按上面 §"🚀 现在可以正式启动 Phase 1" 推进
3. UI 头像收尾后用户会报"UI 完成"信号，那时立刻进路线 A
4. 在等头像期间，可以并行起跑路线 B 的零依赖工件

如果有上下文不清楚，按以下顺序读：
1. 本文件（你已经在读）
2. `video/04-script-plan.md`（剧本契约）
3. `.tasks/ae-theme/ae-light-theme-report.md`（AE 现状）
4. 长期记忆里 `medical_video_demo` / `director_plan_v3` 标签的 memory

**别再问"我们要做什么样的视频"。已经定了。开干。**
