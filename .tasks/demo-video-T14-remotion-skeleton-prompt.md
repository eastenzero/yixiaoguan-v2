# 副窗口任务 · T14 Remotion 总编排项目骨架

> 2026-05-12 凌晨 主对话导演产出
> 目标：搭一个**1920×1080 / 30fps / 4-5 分钟**的 Remotion 项目骨架，让后续往里填素材就能出片
> 当前阶段：所有素材**还在生产中**，本轮**只搭骨架**，不要等素材

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2
```

Remotion 项目位置约定：

```
.tmp/demo-video/remotion/      ← 已存在但只是 PoC，需要重建为正式 1920×1080 项目
```

如果觉得清理 PoC 麻烦，可以直接新建 `.tmp/demo-video/remotion-final/` 平行目录。

---

## 一句话目标

搭好骨架后，**主对话只需把成品素材文件丢到约定路径**（4 段 AE mp4 / 3 段 demo webm / 7 段配音 mp3），跑 `npm run build` 就能出 final.mp4。

---

## 必读的剧本契约

按顺序读这 3 份，**不要拍脑袋自己设计段落结构**：

1. **`@F:\Documents\code\yixiaoguan-v2\video\04-script-plan.md`** — 4-5 分钟分段总规划（v3.1 亮色主题修订）
2. **`@F:\Documents\code\yixiaoguan-v2\video\06-ae-text-final.md`** — AE 段 4 行中文字幕
3. **`@F:\Documents\code\yixiaoguan-v2\video\07-narration-script.md`** — 7 段配音文案（如不存在，主对话 T2 落盘可能命名不同，搜 video/ 目录里 narration / script-narration / voiceover 关键字）

补充参考（v3.1 修订记录）：

4. **`@F:\Documents\code\yixiaoguan-v2\video\05-progress-checkpoint.md`** — 项目接手入口，导演决策摘要

---

## 段落结构（按 v3.1 剧本）

> 总长目标 **4-5 分钟**（240-300s），1920×1080 30fps（7200-9000 帧）

| # | 段名 | 预估时长 | 素材来源 |
|---|---|---|---|
| 1 | **Intro / Hook** | 10-15s | Pexels 紫粒子 stock 视频 ×1（已下载，路径见下） |
| 2 | **AE 概念展示** | 26-34s | 4 段 AE mp4（待 T10b 副窗口产出） |
| 3 | **D1 学生端 demo** | 60-70s | `out/d1/student.webm` ✓ 已就绪 |
| 4 | **D2 教师端 demo** | 50-60s | `out/d2/teacher.webm` ✓ 已就绪 |
| 5 | **D3 双端实时分屏** | 50-60s | `out/d3/student/student.webm` + `out/d3/teacher/teacher.webm` ✓ 已就绪 |
| 6 | **Outro / 价值总结** | 15-20s | 复用 Intro stock 倒放 / 静态背景 + 字幕 |

合计预估 **240-300s**，跟 4-5 分钟目标对齐。

---

## 关键素材路径（输入）

### 已就绪
```
.tmp/demo-video/intro-candidates/      ← 23 个 Pexels 紫粒子候选 mp4
.tmp/demo-video/intro-ranked.json      ← 评分排名
.tmp/demo-video/out/d1/student.webm    (1.81 MB, 64.8s)
.tmp/demo-video/out/d1/events.json     ← 关键事件 timing
.tmp/demo-video/out/d2/teacher.webm    (2.93 MB, 59.0s)
.tmp/demo-video/out/d2/events.json
.tmp/demo-video/out/d3/student/student.webm  (0.95 MB, 45.1s)
.tmp/demo-video/out/d3/student/events.json
.tmp/demo-video/out/d3/teacher/teacher.webm  (1.34 MB, 45.1s)
.tmp/demo-video/out/d3/teacher/events.json
.tmp/demo-video/out/d3/sync.json       ← 关键：双 webm 对齐 metadata
```

### 待填（你做骨架时用占位）
```
.tasks/ae-theme/ae-scene-01.mp4   (8s,  待 T10b 副窗口)
.tasks/ae-theme/ae-scene-05.mp4   (8s,  待 T10b)
.tasks/ae-theme/ae-scene-10.mp4   (10s, 待 T10b)
.tasks/ae-theme/ae-scene-13.mp4   (8s,  待 T10b)
.tmp/demo-video/voice/intro.mp3   (待 T4)
.tmp/demo-video/voice/ae.mp3      (待 T4)
.tmp/demo-video/voice/d1.mp3      (待 T4)
.tmp/demo-video/voice/d2.mp3      (待 T4)
.tmp/demo-video/voice/d3.mp3      (待 T4)
.tmp/demo-video/voice/outro.mp3   (待 T4)
```

---

## D3 双端分屏对齐（最关键的技术细节）

`out/d3/sync.json` 内容：
```json
{
  "task": "T13-D3-dual",
  "conv_id": 162,
  "t0_epoch_ms": 1778518376370,
  "setup_duration_ms": 11230,
  "total_duration_ms": 45115,
  "viewport": { "width": 393, "height": 852 },
  "fps": 30,
  "notes": [
    "两个 webm 视频从同一 t0 开始（context.newContext 后立刻 setupDurationMs 内）",
    "Remotion 应用 setup_duration_ms 修剪两端开头",
    "对齐方法: video.startFrame = round(setup_duration_ms / 1000 * fps)"
  ]
}
```

**Remotion 对齐策略**：双 `<OffthreadVideo>` 并排，各自 `startFrom = round(setup_duration_ms * fps / 1000)`。两个视频从同一墙钟时刻开始，砍掉开头 setup 阶段后就能让 send_msg / recv_msg 在两端时间轴上对齐。

---

## 必做（骨架范围）

### 1. 项目初始化
- `npm init` Remotion 4.x（用 Remotion CLI 模板 `npx create-video@latest --blank`）
- TypeScript（不要 plain JS）
- Tailwind CSS（项目里其他 demo PoC 用的就是 Tailwind，保持一致）
- 中文字体：`@fontsource/noto-sans-sc` 或本地引入思源黑体（保证字幕中文渲染）

### 2. Composition 配置
- `width: 1920, height: 1080, fps: 30, durationInFrames: 8400`（先按 280s 设，后期可调）
- 单一主 composition `<MainSequence />`，内部按 6 段 `<Sequence from={...} durationInFrames={...}>` 分割

### 3. 段落组件骨架
为每段建一个独立 React 组件，先用占位（`<AbsoluteFill bg='#7C3AED'>` + 段名文字），素材到位后再换：

```
src/sections/IntroSection.tsx       ← 占位先用纯紫底 + "Intro 占位"
src/sections/AeSection.tsx          ← 4 个 mp4 串接 + 字幕 overlay（字幕在 ae-text-final.md）
src/sections/D1StudentSection.tsx   ← <OffthreadVideo src=student.webm /> + 字幕 + 配音
src/sections/D2TeacherSection.tsx   ← 类似
src/sections/D3DualSection.tsx      ← 左右两个 <OffthreadVideo>，用 sync.json 对齐 startFrom
src/sections/OutroSection.tsx       ← 占位 + 价值总结字幕
```

### 4. 字幕系统（数据驱动）
不要把字幕硬编码在每段组件里。建一个数据文件：

```ts
// src/data/captions.ts
export type Caption = { from: number; duration: number; text: string; size?: 'lg' | 'md' };

export const captionsBySection: Record<string, Caption[]> = {
  intro: [
    { from: 0, duration: 90, text: '校园里', size: 'lg' },
    { from: 90, duration: 90, text: '问题就该被秒答' },
  ],
  ae: [ /* 从 video/06-ae-text-final.md 拷过来 */ ],
  d1: [ /* 从 video/07-narration-script.md D1 那段拆 */ ],
  d2: [],
  d3: [],
  outro: [],
};
```

字幕组件 `<Captions section="d1" />` 自动按 `useCurrentFrame()` 找当前显示文字。

### 5. 配音轨（Audio sequencing）
每段单独一个 `<Audio src={voiceMp3Path} startFrom={0} />`。占位：先放静音 mp3 或者干脆不放（音轨为空也能 build）。

### 6. 工程化
- `package.json` scripts:
  - `npm run dev` → `remotion preview`（开发预览）
  - `npm run render` → `remotion render src/index.ts MainSequence out/final.mp4`
  - `npm run lint` (optional)
- `README.md` 写：素材路径约定 + 怎么换素材 + build 命令
- `.gitignore` 排除 `out/` `node_modules/` `*.webm` `*.mp3`

### 7. 占位 build 验证
跑一次 `npm run render`，应该能产出一个 280s 长的 mp4（全是占位紫底 + 段名文字）。这就是骨架交付证明。

---

## 不要做的事（骨架阶段）

- ❌ 不要等素材到位才开始（占位先跑通 pipeline 比啥都重要）
- ❌ 不要自己写文案 / 字幕（剧本契约已经定稿，照抄即可）
- ❌ 不要做花哨过场动画（fade in/out + Spring 弹性即可，过场不是核心卖点）
- ❌ 不要重新设计段落结构 / 时长（按 04-script-plan.md v3.1）
- ❌ 不要在主对话之外修改任何 `apps/` `services/` 仓库代码
- ❌ 不要 commit 大体积素材（webm/mp3/mp4），只 commit 源码 + package.json

---

## 验收清单

主对话来验收时会看：

- [ ] `.tmp/demo-video/remotion-final/`（或重建后的 `.tmp/demo-video/remotion/`）完整可跑
- [ ] `npm install` 一次过
- [ ] `npm run dev` 起 preview，6 段都能在时间轴看到，至少占位区分清楚
- [ ] `npm run render` 能产出一个 280s 左右的 mp4（占位即可）
- [ ] `src/data/captions.ts` 已塞好 6 段对应文案（从 06-ae-text-final.md / 07-narration-script.md 抽）
- [ ] `src/sections/D3DualSection.tsx` 已实现 sync.json 双视频 startFrom 对齐逻辑
- [ ] `README.md` 清晰说明：素材替换路径 + 渲染命令 + 时长调整位置

跑完了告诉主对话以下信息：

1. 项目根目录绝对路径
2. `npm run render` 出的占位 mp4 路径 + 总时长
3. 你做骨架时是否调整了 04-script-plan.md 的段落时长（如果是，告诉主对话哪段改了多少）
4. 你认为可能 block 后续填素材的疑难点（比如 webm 编码格式不被 Remotion 支持等）

---

## 卡壳怎么办

如果遇到下列任一情况就**停下来回报主对话**：

- Remotion 4.x 装不上（npm 网络 / 版本冲突）
- `<OffthreadVideo>` 加载 webm 报错（可能需要 ffmpeg 转 mp4 中间产物）
- Tailwind 跟 Remotion 集成出问题
- sync.json 对齐算出来双视频对不上（让主对话查 sync.json metadata）
- 任何超出 90 分钟的卡壳

回报时附上：错误日志 + 当前进度 + 你尝试过的方案。
