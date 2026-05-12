# 副窗口任务 · T16 Screen Studio 风格 + AE Logo Reveal 整合

> 2026-05-12 13:40 UTC+8 主对话导演
> 上下文：T15 整片电影感升级已交付（35.61 MB / 240.04s），但用户反馈"动效一般"
> 用户原话："我希望的是 Screen Studio 那种缩放的风格 目前这一版做的还比较粗糙 也没有屏幕聚焦鼠标的那种感觉"
> 同时 AE 副窗口交付了 Logo Reveal 5s 4K mp4，本轮一并整合

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\remotion-final\
```

---

## 一句话目标

**把 T15 那种"固定时间窗、固定位置"的 zoom 升级成 Screen Studio 风格的"事件驱动、焦点跟随"动态 zoom + pan + 鼠标光标 + 点击涟漪。同时把 AE Logo Reveal 5s 整合进 Intro。**

---

## 上下文：T15 现状 + 用户期望差距

### T15 做的（已交付，但用户认为"粗糙"）

```ts
// 当前 D1StudentSection.tsx 风格：
const scale = interpolate(frame, [480, 510, 930, 960], [1, 1.15, 1.15, 1]);
const transformOrigin = "50% 30%";  // 固定一个位置
```

→ 固定时间窗（16s 开始 zoom-in，32s 开始 zoom-out）、固定一个 transform-origin（上半 30%）、固定一个 scale 范围。

### 用户想要（Screen Studio 标准）

```
1. 焦点跟随 —— 学生 tap "宿舍电费"chip 时 zoom 到那个 chip (x=103, y=271)
   AI 流答开始时 zoom 到 .msg-bubble.ai-bubble 区域
   点开来源时 zoom + pan 到 .cit-item 位置 (x=181, y=445)
   
2. 鼠标光标 —— webm 里没有鼠标（Playwright 默认不录），需要 Remotion 合成
   一个 macOS 风格的箭头 / 圆点光晕跟着 events.json 的焦点位置移动
   
3. 点击涟漪 —— 每个 tap event 时刻在 (x, y) 出现 expanding ring + opacity decay
   
4. 平滑缓动 —— 焦点切换不是硬切，是 bezier ease-in-out 平滑过渡（0.4-0.8s）
   
5. 设备相框（可选）—— macOS 风格 phone frame + outer shadow + 浅紫白底
```

---

## 关键发现：events.json 已经包含所有数据

每个 D1/D2/D3 录屏脚本都生成了完整的事件日志，**含 tap 坐标 + 选择器 + 时间戳**：

### 文件位置

```
.tmp/demo-video/out/d1/events.json          (4.5 KB)
.tmp/demo-video/out/d2/events.json          (5.3 KB)
.tmp/demo-video/out/d3/student/events.json  (1.3 KB)
.tmp/demo-video/out/d3/teacher/events.json  (4.0 KB)
```

### 事件 schema 示例（D1 真实片段）

```json
{
  "viewport": { "width": 393, "height": 852 },
  "fps": 30,
  "events": [
    { "time_ms": 8757, "type": "tap", "label": "快捷 chip: 宿舍电费",
      "selector": ".tag-chip", "x": 103, "y": 271 },
    { "time_ms": 13047, "type": "ai_streaming_start",
      "selector": ".msg-bubble.ai-bubble" },
    { "time_ms": 18948, "type": "ai_streaming_end",
      "samples": 38, "final_height": 598 },
    { "time_ms": 21811, "type": "tap", "label": "点开来源",
      "selector": ".cit-item", "x": 181, "y": 445 },
    { "time_ms": 4221, "type": "scroll", "direction": "h", "delta": 120 }
  ]
}
```

→ **数据完备**：每个用户操作都有 time_ms + x/y + selector + label。你不需要重新录制，直接 import JSON 驱动。

---

## P0 · Screen Studio 风格的 D1/D2/D3 段重做

### 实现思路（不强制，仅供参考）

1. **新 helper**：`src/data/focusTimeline.ts`（或类似）
   - 读取 events.json（用 staticFile import 或 Composition 启动时 fetch）
   - 把 `tap` / `ai_streaming_start` 等事件转换成 **FocusFrame 序列**
   - 每个 FocusFrame: `{ frame, x, y, scale, holdFrames }`

2. **新组件**：`src/components/ScreenStudioWrapper.tsx`
   - 包裹 `<OffthreadVideo>` 的 webm
   - 根据 useCurrentFrame() 查 FocusFrame 序列
   - 用 spring() 或 bezier 平滑插值当前 transform: scale + translate
   - transform-origin 跟着 (x, y) 动态变（注意 (x, y) 是 viewport 393×852 坐标，Composition 是 1920×1080，需要 scale 换算）

3. **鼠标光标合成层**：
   - 加一个 absolute positioned div 跟着 (x, y) 移动
   - 视觉：macOS 箭头 SVG（黑底白边）+ 后面跟一个 24px 圆形 spotlight（白色 50% opacity + radial blur）
   - 或者更"Screen Studio"风格：一个 16px 的彩色圆点 + 周围 expanding ring 高亮焦点
   - 鼠标在 tap 之间的"空闲时间"也存在，但用更淡的 opacity（说明用户在阅读）

4. **点击涟漪**：
   - tap event 时间点叠加一个 expanding ring（从 0 → 60px 半径，opacity 1 → 0，duration 0.5s）
   - 配合 0.1s 短"吸气"音效（如果想加，可选）

5. **焦点缓动节奏**：
   - 焦点从 A → B 切换时，0.4-0.6s bezier ease-in-out 完成
   - 焦点到达后 hold（直到下一个 event）
   - hold 期间 scale 微微呼吸（1.0 → 1.02 → 1.0 周期 4s）防止画面"死"

6. **scale 策略**：
   - 默认 1.0（全屏概览，能看清"在用什么页面"）
   - tap 触发后 zoom 到 1.5-1.8（精读 UI 细节）
   - hero 操作（AI 流答 / 实时推送）zoom 到 1.4（够看清气泡气泡内文字）
   - 不要超过 2.0（webm 是 viewport 393×852 在 1920×1080 里已经被放大，再 zoom 2x 会糊）

### 三段处理优先级

| 段 | 时长 | 复杂度 | 备注 |
|---|---|---|---|
| **D1** 学生端 | 65s | 中 | 8 个 tap event，事件清晰，最容易出效果 |
| **D2** 教师端 | 60s | 中 | 多 tab 切换 + dashboard，焦点多 |
| **D3** 双端 | 50s | 高 | 双 webm，每端独立 events.json，需要协同。**可以只对两端中各一段做焦点跟随**（如学生发消息时焦点在学生 phone 内，教师收到时焦点切到教师 phone 内），其余时间用 T15 现成的 Beam zoom 保持 |

### 不要做的事（D1/D2/D3 重做相关）

- ❌ 不要重新录制 webm（events.json 已够用，重录 30+ 分钟一次太贵）
- ❌ 不要改 events.json（这是数据源，只读）
- ❌ 不要改 D1/D2/D3 段时长（仍 65/60/50）
- ❌ 不要把焦点切换做得太多太快（每段 5-10 个焦点切换为佳，不要把每个 pause/scroll 都做焦点）
- ❌ 不要把 scale 调过头（最多 1.8x，太大 webm 锯齿明显）
- ❌ 不要为了"动效炫"覆盖字幕（字幕仍然是导演叙事主线，焦点跟随是辅助）

---

## P0 · AE Logo Reveal 5s 整合

### 素材

AE 副窗口本轮交付的新片头：

```
F:\Documents\code\yixiaoguan-v2\.tasks\ae-theme\render-segments\logo-reveal.mp4
  - 时长 5s
  - 4K (3840×2160)
  - 30fps
  - H.264 mp4 直出
  - 内含：3D 描摹 logo 入场动画 + tagline 浮现
```

复制到 `.tmp/demo-video/ae-scenes/logo-reveal.mp4` 或类似位置，挂到 `paths.ts`：

```ts
// 新增字段
logoReveal: staticFile('ae-scenes/logo-reveal.mp4') as string | null,
```

### 整合位置：替换 Intro 前 5s

**导演决策**：保持整片总长 240s，logo reveal 5s 替换 Intro 0-5s 的"LightBackdrop 呼吸 blob"段。

新 IntroSection 节奏：

| 时段 | 内容 | 实现 |
|---|---|---|
| **0-5s** | Logo Reveal mp4 | `<OffthreadVideo src={logoReveal} />` 占满 |
| **5-8s** | crossfade 1s + LightBackdrop 浮现 + BGM 维持 | logo 末尾透出底色，过渡到 LightBackdrop |
| **5-13s** | "医小管 / Yi Xiao Guan · 智慧校园助理" hero 字幕 + 浅色 backdrop（保留原 T15 设计） | Captions intro 段不动 |
| **13s** | 段切换到 AE | 原有转场不动 |

**衔接关键点**：
- logo-reveal.mp4 的最后 0.3s 应该跟 LightBackdrop 的 backdrop 颜色对齐（浅紫白），避免硬切感
- 如果 logo-reveal 末尾不是浅紫白底，用一个 0.5s crossfade overlay 兜底（mp4 淡出 + LightBackdrop 淡入）

### Logo PNG 也用上

用户已经处理好了 Logo PNG：

```
.tasks\ae-theme\logo-yxg-4k.png  (透明底 PNG, 6688×3764)
```

复制到 `.tmp/demo-video/brand/logo.png`（你 T15 已经预留接口 `brandLogo`），用户落盘到这个路径后：
- `paths.ts` 里 `brandLogo: staticFile('brand/logo.png')` 自动生效
- **Outro Phase C** 168×168 hero 位置会自动出现真实 logo（替代 T15 的纯文字 fallback）

如果你做整合时发现 brand/logo.png 已落盘，直接接入。

### 不要做的事（AE 整合相关）

- ❌ 不要用 `ae-combined.mp4`（40s 合并版），AE 5 段独立 mp4 路径已对接，保持原状
- ❌ 不要改 Intro 字幕文案（"医小管 / Yi Xiao Guan · 智慧校园助理"不动）
- ❌ 不要改 Intro 总时长（仍 13s，logo reveal 是放在前 5s 内）
- ❌ 不要在 logo reveal 上叠加 Captions（logo mp4 自带 tagline，不要叠）

---

## P1 · Outro 微调（如果 logo.png 落盘了）

T15 已经做了 Outro 5 阶段蒙太奇 + hasAsset() 接口预留。本轮只需：

1. 检查 `.tmp/demo-video/brand/logo.png` 是否存在
2. 如存在：`paths.ts` 改 `brandLogo: staticFile('brand/logo.png')` 一行
3. 确认 Outro Phase C 168×168 logo 区域正确显示真实 logo（不是纯文字 fallback）
4. 必要时微调 logo 上下文字间距（视觉验证）

如不存在：保持 T15 现状（纯文字 hero），不强求。

---

## P2 · 锦上添花（可选，看时间）

### 1. 设备相框（macOS phone frame）

Screen Studio 的标志性视觉之一：把 webm 包在 macOS 风格的圆角矩形 phone frame 里，外面留 padding + 阴影。

- 圆角 ~40px（iPhone 14 Pro 风格）
- 外边距 ~80px（视觉呼吸）
- 投影 `box-shadow: 0 40px 80px rgba(91,33,182,0.15)`
- 浅紫白底（跟整片 backdrop 统一）

⚠️ **代价**：webm 内容会缩小（因为外层加了 padding），相当于全片清晰度下降一点。如果做了，确保焦点 zoom 范围扩大（不然画面会显得更小）。

⚠️ **D3 段不要做相框**（双 phone 已经够拥挤）。

### 2. 键盘提示浮窗

Screen Studio 在用户按 Enter / 输入字符时浮现按键提示。我们 events.json 没记录键盘事件（只有 tap），跳过。

### 3. 焦点之间的"音效 ping"

每个 tap event 时刻播一个 0.1s 短电子音（类似 macOS 的 click 声）。可选，看时间。

### 4. 鼠标光标的不同状态

- 默认：箭头
- hover：手型
- click：箭头 + ring expanding
- 流答期间：光标淡出（说明 AI 在工作，用户在看）

---

## 不要做的事（整体守则）

- ❌ 不要改 tagline / 配音文案（"医小管 / 智慧校园助理"不动，"医管智枢"目前只在 AE Logo Reveal 内出现 5s，不进 Remotion 字幕系统）
- ❌ 不要重做配音（5 段 mp3 都用现有的）
- ❌ 不要改字幕文案（captions.ts 文案不动）
- ❌ 不要改段总时长（240s 锁定，段长 13/34/65/60/50/18 不动）
- ❌ 不要重渲超过 4 次（每次 16-20 分钟，本任务工程量大需要节制）
- ❌ 不要破坏 T15 的成果（段间转场 / Outro 蒙太奇 / 字幕 spring 入场 都保留）
- ❌ 不要为做 Screen Studio 引入庞大依赖（Remotion 原生 spring + interpolate 够用；如真需要 framer-motion 等，先评估）

---

## 验收清单

主对话验收会做：

### 必看（P0 Screen Studio）
- 跳到 D1 段（13-78s），观察是否有"鼠标光标跟着 tap event 移动 + 点击涟漪 + 焦点 zoom + pan"
- 关键 event 时刻是否到位：
  - D1 8.7s "tap chip" → zoom 到 chip 位置
  - D1 13s "AI streaming start" → zoom 到气泡区
  - D1 21.8s "tap 来源" → pan + zoom 到 citation
- 焦点切换是否平滑（bezier ease-in-out，不是硬切）
- 鼠标光标视觉是否舒服（不要太大、不要太花哨）

### 必看（P0 Logo Reveal 整合）
- Intro 0-5s 是否播放 logo-reveal.mp4
- 5-13s 是否平滑过渡到 LightBackdrop + 字幕 hero（不要硬切）
- 整片仍精确 240s

### 看可选项（P2）
- 设备相框（如做了，看视觉是否优雅、是否覆盖字幕）
- 键盘 ping 音效（如做了，不要突兀）

### 性能 / 正确性
- `npm run render` 完整跑过
- 整片仍精确 240s（容差 ±0.5s）
- 文件大小 < 100 MB（焦点跟随 + 鼠标层会增大，但不应翻倍）
- 没引入新 P0 bug

### 回报内容
跑完了告诉主对话：
1. 改了哪些 .tsx / .ts 文件（路径列表）
2. Screen Studio 实现核心架构（FocusTimeline 数据流 + ScreenStudioWrapper 组件 + 鼠标层），3-5 句话
3. 每段焦点事件数（D1 几个 / D2 几个 / D3 几个）
4. 鼠标光标视觉选择（箭头 / 圆点 / 其他）
5. AE Logo Reveal 跟 Intro 的衔接做了什么（crossfade 长度 / 颜色匹配）
6. 是否接入了 logo.png（Outro Phase C 是否成功显示真 logo）
7. P2 做了哪些
8. 重渲后 final-fast.mp4 路径 + 大小 + 渲染耗时
9. **你认为最值得 highlight 的 3 个 Screen Studio 时刻**（哪三处用户一定要看）
10. 你认为最难做 / 妥协最多的点（坦白说）

---

## 卡壳怎么办

- events.json 里 (x, y) 是 viewport 393×852，但 Remotion Composition 是 1920×1080 → 换算：webm 在 Composition 内被等比缩放显示，先量出 webm 的渲染 rect (left, top, width, height) 在 Composition 里的位置，再把 viewport (x, y) 映射进来：`compX = rect.left + (x / 393) * rect.width`
- 焦点 zoom 后 webm 边缘被裁掉 → 给 webm wrapper 加 `overflow: hidden`，或缩小 zoom max（1.5x 而不是 1.8x）
- 鼠标光标在 viewport 边缘超出 → clamp 到 [0, 393] / [0, 852] 之间
- AE Logo Reveal mp4 末尾色不是浅紫白 → 加 0.5s 黑/白/紫 overlay crossfade 兜底
- 整片渲染时间超 30 分钟 → concurrency 拉高、jpeg-quality 降到 60、必要时砍 P2 项
- 任何超 3 小时卡壳 → 立刻回报附 git diff + 屏幕截图

完成后这是 Phase 1 整片的 v1.1，离"导演满意"差不多了。等用户最后一遍审片后定稿。
