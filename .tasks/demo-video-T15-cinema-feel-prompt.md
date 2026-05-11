# 副窗口任务 · T15 整片电影感升级 + Outro 重做

> 2026-05-12 05:40 UTC+8 主对话导演
> 上下文：所有 P0 / P1 bug 已修完，整片 `final-fast.mp4`（32.6 MB / 4:00:04）已经"足够 polish 给老板看"。本任务把"polish"再推到"电影感"。
> 用户原话："现在可以专注于 Remotion 这边的动效优化了 / 最后的那个片尾结束也用 Remotion 来制作 / AE 这边做起来实在是太费劲了 20 分钟才渲染了 5 秒"

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\remotion-final\
```

---

## 一句话目标

把当前"对齐准、bug 干净"的整片，升级成"有电影感、有节奏感、有品牌仪式感"的 1.0 版。Outro 完全重做，整片关键时刻加 zoom/焦点/弹性入场。

---

## 当前现状（你做之前要知道）

- **整片 240s = 6 段（intro 13 / AE 34 / D1 65 / D2 60 / D3 50 / outro 18）** 节奏锁定，**不要改段时长**
- **所有素材到位**：5 段配音、4 段 webm、5 段 AE mp4、字幕全段、浅色主题统一、文字虚拟化（学生→林小满）
- **当前所有段**：基本是"视频/背景 + 字幕叠加 + 配音"的极简结构，**没有任何 zoom / 转场 / 弹性入场 / focus 框**
- **当前所有 Captions 入场**：simple fade `[0, 12]` 0→1，simple fade `[duration-12, duration]` 1→0
- **当前所有段切换**：硬切（一帧切下一帧）
- **当前 Outro**：浅色径向 backdrop + slogan + "2026 · A YXG PRODUCTION" credit，仪式感不足

---

## P0 必做 · Outro 完全重做

**用户原话回放**："最后的那个片尾结束也用 Remotion 来制作"

### 期望（你自由发挥）

把 18s Outro 升级成有仪式感的"片尾蒙太奇"。建议结构（不强制）：

```
0-3s    背景从前一段淡入，呼吸感 LightBackdrop 出现
3-7s    "让校园里的每一个问题" 大字 stylized 入场（spring 弹性 / typewriter / sliding mask）
7-12s   "都被认真对待" 接续大字，跟上句形成节奏对比
12-15s  品牌字 "医小管" 巨大 hero 出现 + 副标 "智慧校园助理"
15-18s  "2026 · A YXG PRODUCTION" credit + 浅色背景余韵收束（淡到白底）
```

### 必加元素

- **Logo 占位**：用户会自处理 logo PNG 落盘到 `.tmp/demo-video/brand/logo.png`。你**先用"医小管"中文字代替**（96px 巨大字号，深紫 #5B21B6，配 SVG-feel 边框装饰）。**保留接口**：在 `paths.ts` 加 `brandLogo: hasAsset('brand/logo.png') ? staticFile('brand/logo.png') : null`，用户素材到位后改一行即可生效
- **stylized 字幕入场**：放弃 simple fade，用 Remotion `spring()` 或 `interpolate` + bezier easing，做"上滑入场 + 弹性回弹"或"打字机逐字 reveal"
- **品牌 brand close**：最后 3s 必须有"收束感"（背景慢慢淡到纯白 / blob 慢慢消失 / credit 字幕居中出现），让观众明确知道"片子结束了"

### 不要做

- ❌ 不要保留当前 Outro 的"5 blob 径向背景 + slogan + credit 静态三件套"（要重写）
- ❌ 不要改 outro 段时长（仍 18s）
- ❌ 不要改 voiceOutro 配音引用
- ❌ 不要给 outro 加 BGM（BGM 是整片底铺，另说）

---

## P1 整片动效（必做，按优先级）

### 1. 段间转场（消灭硬切）

6 段之间的边界目前是硬切，电影感最基础就是不要硬切。在 `Composition.tsx` 的 `<Sequence>` 之间或每个 Section 内部首尾 12-20 帧做：

- **crossfade**：当前段末尾 0.5s 渐隐 + 下一段开头 0.5s 渐入
- 或 **wipe / slide**：拿主色 `#7C3AED` 做一个一闪而过的 mask
- 或 **white flash**：0.3s 白闪然后下一段进入（仅在 AE → D1 这种"剧情切换"点用，不要每段都用）

建议节奏：
- intro → AE：crossfade（同浅色调，过度自然）
- AE → D1：white flash 或 short slide（从"产品理念"切到"实操演示"，需要 punctuation）
- D1 → D2：crossfade（学生 → 教师，同色调过度）
- D2 → D3：slide-up（教师后台 → 双端实时，"打开新维度"感）
- D3 → outro：long crossfade（"高潮收束"感）

### 2. 字幕入场升级

所有 `<Captions>` 组件的 fade 行为升级。改 `components/Captions.tsx`：

- **入场**：用 `spring()` 做"上滑 + 弹性"（translateY: 30 → 0, opacity: 0 → 1，spring config: damping 200, stiffness 200, mass 0.5 这种参数自调）
- **退场**：可以保留 simple fade（避免过度炫技）
- **size="hero"**：可以加额外的"逐字 reveal"（字符级 stagger），让 "医小管" / "让校园里的每一个问题" 这种主 hero 字幕更有仪式感
- **size="sm"** / **size="md"**：保持低调，spring 但 amplitude 小

### 3. 关键 zoom 特写（3 处至少）

在 D1/D2/D3 三段中，选 3 个 hero 时刻做 `transform: scale(1) → scale(1.15)` 的 zoom-in 强调（zoom 进特定区域，做特写）：

**建议时刻**：
- **D1 段 16-32s**："AI 流式回答"时段，zoom 到 webm 上半部分（气泡所在区域）
- **D2 段 10-30s**："数据看板 847 / 73.2%" 段，zoom 到 dashboard 数字区域
- **D3 段 22-37s**："端到端 < 200ms" 段，zoom 到 Beam 区域 + 左右两端轻微缩小

技术：在 Section 组件里给 `<OffthreadVideo>` 加 `transform: scale(...)` + `transform-origin`，用 `interpolate(frame, ...)` 在 zoom-in 时间窗内做 scale 动画。注意不要 zoom 到 webm 内容被裁掉太多（边缘要 mask / 留白）。

---

## P2 锦上添花（可选，看时间）

如果 P0+P1 做完还有时间，按性价比挑：

### 4. focus 框 callout

在关键瞬间叠加一个紫色 outline ring（绝对定位 div + border 2px solid `#7C3AED` + border-radius 12px + animated scale/opacity）。例如：
- D1 32s "点开来源" 时刻：在 webm 上"来源链接"位置叠 ring + 0.8s 后淡出
- D2 50s "实时受理就绪"：在某个按钮位置叠 ring

### 5. 数字浮层（D2 数据看板）

D2 dashboard 上的 "847 提问" / "73.2% AI 解答率" 在 webm 里是固定数字。可以叠 Remotion 文字层完全覆盖原数字，做"从 0 滚动到 847"的 counter 动画（`interpolate(frame, [from, to], [0, 847])` + `Math.round()`）。

⚠️ **位置对齐挑战大**：webm 里数字在某 x,y 像素位置，Remotion 浮层要精确覆盖（用 absolute positioning + 微调 padding）。**如果对齐有偏差，立刻放弃这一项**，原 webm 数字也 OK 看。

### 6. D1/D2 滚动加速段

D1 home 16 项卡片滚动段、D2 dashboard 各 tab 切换段，可以用 `<OffthreadVideo>` 的 `playbackRate=1.5` 做 1.5x 加速（让"扫一眼"动作不拖时间）。

⚠️ **影响**：会让段总时长变短，需要在 Section 内部用空帧填补到段长不变。**只在 hero shot 之间的"过场段"加速**，不要在重点段加速。

### 7. D3 PIP picture-in-picture

D3 段当主旁白讲到"学生发出" / "老师接到"时，强调一端 + 另一端缩小到角落（PIP 风格）。这个工程量大，**最后再考虑**。

---

## 条件触发（用户素材到位后再做）

### 8. Logo 接入

用户会自处理 logo，落盘到：
```
.tmp/demo-video/brand/logo.png   （透明底 PNG，≥ 1024×1024）
```

落盘后：
- 在 `paths.ts` 加 `brandLogo: hasAsset('brand/logo.png') ? staticFile('brand/logo.png') : null`
- Intro 段中前 5s 不出 logo（保留"匿名出场"悬念），5-13s logo 跟"医小管"文字一起淡入
- Outro 段 12-15s 区段（参考 P0 重做结构）放 logo hero 出现 + 副标

**逻辑**：用 `hasAsset()` 兜底，logo 没到位时 fallback 到"医小管"中文字（你 P0 Outro 重做时已经写好）。

### 9. BGM 接入

用户会找 BGM 落盘到（推测）：
```
.tmp/demo-video/bgm/main.mp3  或类似
```

落盘后：
- 在 `paths.ts` 把 `bgm` 字段指向新文件
- IntroSection 里 `<Audio src={ASSETS.bgm} volume={0.6} />` 已经预留，直接生效
- 但需要在所有 Section 里都加（不只是 Intro），让 BGM 贯穿整片
- 配音段（AE/D1/D2/D3/Outro）BGM 音量降低到 0.15-0.25，无配音段（Intro）BGM 音量 0.5-0.6
- 用 `useCurrentFrame()` + 整片相对帧位置做"配音处时 ducking"

⚠️ **不要在用户 BGM 没到之前盲加 BGM 引用**。等用户落盘后再加。

---

## 不要做的事

- ❌ 不要改段总时长（240s / 段长 13/34/65/60/50/18 都不动）
- ❌ 不要改配音引用（5 段 mp3 路径不动）
- ❌ 不要改字幕文案（captions.ts 文案不动，只改入场动画）
- ❌ 不要改 webm / AE mp4 文件本身（只能在 Section 组件里叠加 / zoom / transform）
- ❌ 不要改设计令牌（tokens.ts 的颜色 / 字号 / 字体不动，要新加令牌可加，但不要改现有）
- ❌ 不要重渲超过 3 次（每次重渲 10-30 分钟，节制使用）
- ❌ 不要为做动效引入新 npm 依赖（除非 Remotion 不带的，比如 `@react-spring/web` —— 但 Remotion 自带 spring()，足够用）
- ❌ 不要在没看完整片 final-fast.mp4 之前盲改（先看 1 遍现状 + 看哪几处最需要电影感）

---

## 验收清单

主对话验收会做：

### 必看（P0 + P1）
- Outro 18s 完整看一遍：仪式感强 / slogan stylized / 品牌字出现 / credit 收束 / 不再是当前的"静态三件套"
- 6 段间转场：硬切消灭，最好每段切换都有 0.5s 左右的过渡
- 字幕入场：所有 Captions 看上去"弹"而不是"淡"
- 3 处 zoom 特写：D1 AI 气泡 / D2 dashboard 数字 / D3 Beam 区域 至少有 2 处看到 scale 强调

### 看可选项（P2 看你做了哪些）
- 数字浮层（D2 dashboard）：如做了，看对齐是否完美
- focus 框：如做了，看是否在正确瞬间出现
- 加速段：如做了，看是否在"过场段"用，不影响重点 shot

### 性能 / 正确性
- `npm run render` 完整跑过（用 `--codec h264-mkv` 或 `mp4` 都行）
- 整片仍精确 240s（容差 ±0.5s）
- 文件大小 < 80 MB（动效叠加会增大，但不应翻倍）
- 没有引入新 P0 bug（如字幕错位、视频卡顿、音视频不同步）

### 回报内容
跑完了告诉主对话：
1. 改了哪些 .tsx 文件（路径列表）
2. P0 Outro 重做：核心结构描述（5 句话即可）
3. P1 段间转场：用了什么转场方式（crossfade / wipe / slide）
4. P1 字幕入场：用了 spring 还是 bezier，是否做了字符级 stagger
5. P1 zoom 特写：做了哪 3 处，scale 范围（如 1 → 1.15）
6. P2 做了哪些可选项（带"完成 / 放弃"标记）
7. logo + BGM 接口是否预留好（用户后续直接落盘文件即可生效）
8. 重渲后的 final-fast.mp4（路径 + 大小 + 渲染耗时）
9. 你认为最值得 highlight 的 3 个细节

---

## 卡壳怎么办

- spring config 调出来过冲太大 / 弹太久 → damping ↑ stiffness ↓，文档 https://www.remotion.dev/docs/spring
- zoom-in 把 webm 边缘裁掉了 → 调整 `transform-origin` 到 zoom 中心点，或者给 wrapper 加 `overflow: hidden` 但 webm 加 `object-fit: cover`
- 数字浮层位置永远对不齐 → 放弃 P2 第 5 项，写到回报里"放弃"原因
- 字幕 spring 入场跟配音节奏对不上（配音字快到了字幕才弹完） → 把 spring duration 缩短到 8-12 帧，不要 18 帧
- 任何超 2 小时卡壳 → 立刻回报，附 git diff + screenshot

完成后这是 Phase 1 整片的最终版（除非用户后续要内容修改），等用户 logo + BGM 到位后再小幅迭代一次即可收工。
