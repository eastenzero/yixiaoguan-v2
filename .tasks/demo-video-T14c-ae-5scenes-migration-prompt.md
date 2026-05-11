# 副窗口任务 · T14c Remotion AE 段从 4 → 5 SCENE 迁移

> 2026-05-12 03:10 UTC+8 主对话导演
> 上下文：AE 副窗口取得重大进展，从原 4 SCENE（01/05/10/13）换成 5 SCENE（23/11/18/28/30），且**字幕由 AE 自己出**
> 本任务：Remotion 项目侧同步这两个变化

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\remotion-final\
```

---

## 一句话目标

把 Remotion AE 段从 4 SCENE 配置迁移到 5 SCENE 配置 + **取消 AE 段的 Remotion 字幕叠加**（因为 AE 副窗口的 mp4 自带 Text Holder 文字）。

---

## 上下文：现状 + 决策

### AE 副窗口产出（**已定稿**）

5 个主 SCENE mp4（命名按 SCENE 编号），渲完后会复制到：

```
.tmp/demo-video/ae-scenes/ae-scene-23.mp4   (6s, 开场 · 学生首页)
.tmp/demo-video/ae-scenes/ae-scene-11.mp4   (8s, 核心 · AI 对话)
.tmp/demo-video/ae-scenes/ae-scene-18.mp4   (8s, 对比 · 学生×教师)
.tmp/demo-video/ae-scenes/ae-scene-28.mp4   (6s, 全景 · 五屏)
.tmp/demo-video/ae-scenes/ae-scene-30.mp4   (6s, 收尾 · 服务+数据)
合计 34s = AE 段时长
```

**每个 mp4 自带 Text Holder 文字**（大标题 + 副标题，深紫 #5B21B6 微软雅黑）。

### 字幕策略 reverse

**之前**：`AeSection.tsx` 渲染 `<Captions section="ae" />`，Remotion 在 AE 占位画面上叠"智能问答 · 秒答常见问题"等 4 句字幕

**现在**：AE mp4 自带文字 → Remotion 不再叠 → **取消 `<Captions section="ae" />`**，否则双层文字重叠

---

## 必做的 4 件事

### 1. 更新 `src/data/paths.ts`

把 aeScene01/05/10/13 → aeScene23/11/18/28/30

```ts
// 旧（删）：
aeScene01: null,
aeScene05: null,
aeScene10: null,
aeScene13: null,

// 新（建议）：
aeScene23: staticFile('ae-scenes/ae-scene-23.mp4') as string | null,
aeScene11: staticFile('ae-scenes/ae-scene-11.mp4') as string | null,
aeScene18: staticFile('ae-scenes/ae-scene-18.mp4') as string | null,
aeScene28: staticFile('ae-scenes/ae-scene-28.mp4') as string | null,
aeScene30: staticFile('ae-scenes/ae-scene-30.mp4') as string | null,
```

由于 AE 副窗口还在渲（30-60 分钟），**先把这 5 个赋值为 `null`**（占位），等 mp4 落盘后再改成 `staticFile(...)`。占位时 AeSection 应该自动 fallback 到 PlaceholderFill（沿用现有 `hasAsset()` 机制）。

`publicDir` 是 `..` 即 `.tmp/demo-video/`，所以 `staticFile('ae-scenes/ae-scene-XX.mp4')` 对应 `.tmp/demo-video/ae-scenes/`，不需要改 publicDir 配置。

### 2. 更新 `src/sections/AeSection.tsx`

#### 改 AE_SCENES 数组

```ts
// 旧（删）：
const AE_SCENES = [
  { id: "ae-01", from: 0, duration: 8 * FPS, asset: ASSETS.aeScene01, label: "SCENE_01" },
  { id: "ae-05", from: 8 * FPS, duration: 8 * FPS, asset: ASSETS.aeScene05, label: "SCENE_05" },
  { id: "ae-10", from: 16 * FPS, duration: 10 * FPS, asset: ASSETS.aeScene10, label: "SCENE_10" },
  { id: "ae-13", from: 26 * FPS, duration: 8 * FPS, asset: ASSETS.aeScene13, label: "SCENE_13" },
];

// 新：
const AE_SCENES = [
  { id: "ae-23", from: 0 * FPS,  duration: 6 * FPS,  asset: ASSETS.aeScene23, label: "S23 开场" },
  { id: "ae-11", from: 6 * FPS,  duration: 8 * FPS,  asset: ASSETS.aeScene11, label: "S11 核心" },
  { id: "ae-18", from: 14 * FPS, duration: 8 * FPS,  asset: ASSETS.aeScene18, label: "S18 对比" },
  { id: "ae-28", from: 22 * FPS, duration: 6 * FPS,  asset: ASSETS.aeScene28, label: "S28 全景" },
  { id: "ae-30", from: 28 * FPS, duration: 6 * FPS,  asset: ASSETS.aeScene30, label: "S30 收尾" },
];
// 合计 34s = 1020 frames = 跟 sections.ts 的 AE 段长一致
```

#### 删除 `<Captions section="ae" />` 行

```tsx
// 旧（删）：
<Captions section="ae" variant="onLight" />

// 新：删掉这一行（AE mp4 自带文字）
```

保留 `<Audio src={ASSETS.voiceAe} />` 不变（配音独立于 AE mp4 之外）。

### 3. 更新 `src/data/captions.ts`

清空 `ae:` 段：

```ts
// 旧（删）：
ae: [
  { from: s(0), duration: s(8), text: "智能问答 · 秒答常见问题", ... },
  { from: s(8), duration: s(8), text: "AI 流式回答", ... },
  { from: s(16), duration: s(10), text: "学生有问 · 老师在场", ... },
  { from: s(26), duration: s(8), text: "全场景洞察", ... },
],

// 新：
ae: [],
// AE 字幕由 AE 副窗口在 mp4 内嵌（Text Holder + 微软雅黑 + 深紫 #5B21B6）
```

保留 d1/d2/d3/intro/outro 字幕**不动**。

### 4. 更新 `README.md` 素材路径说明

把 README 里写 "AE 4 段" 的地方改成 "AE 5 段"，列出新的 5 个 SCENE 编号和时长。

---

## 不要做的事

- ❌ 不要改 `src/data/sections.ts` 的 AE 段总时长（仍 34s）
- ❌ 不要改其他段（intro / d1 / d2 / d3 / outro 都不动）
- ❌ 不要改 AE 段的 `<Audio src={ASSETS.voiceAe} />` 配音引用
- ❌ 不要试图自己渲 AE mp4（AE 副窗口负责）
- ❌ 不要改 `tokens.ts` / 配色 / 字体（这一轮纯配置迁移）
- ❌ 不要改 `Captions.tsx` 组件本身（其他段还在用）

---

## 验收清单

1. **paths.ts**：5 个新 ae 字段名 + null 占位（或 staticFile 引用，看 AE 副窗口产出时机）
2. **AeSection.tsx**：AE_SCENES 数组 5 项，时长 6/8/8/6/6 = 34s，无 Captions 叠加
3. **captions.ts**：`ae: []` 空数组
4. **README.md**：素材清单更新到 5 SCENE
5. **`npm run render` 一次过**（如果 AE mp4 还没落盘，应渲出"AE 段 5 个 placeholder + 配音 + 整片其他段不变"的版本）
6. **占位渲出来后看一眼**：AE 段不应再出现"智能问答 · 秒答常见问题"等字幕（因为 captions.ae 清空 + AeSection 删了 Captions），只有 PlaceholderFill 的占位"S23 开场" 等 label

跑完了告诉主对话：
1. 改了哪几个文件 + 一行 git diff 摘要
2. 占位重渲后 final-fast.mp4 路径 + 文件大小
3. AE 段的 5 个 placeholder 截图（任意帧），主对话好快速比对节奏
4. 是否引入新 type 或破坏现有 TS 类型（应该不会）

---

## 卡壳怎么办

- AE 副窗口的 mp4 还没出来 → 不影响本任务，先用 null 占位完成 paths 迁移
- TS 类型报错（如 `ASSETS.aeScene23` 不存在）→ 检查 paths.ts 是否完整改完
- `<Captions section="ae" />` 删了之后 captions.ts 里 `ae` 字段不能为 undefined（TS 强类型） → 保留 `ae: []` 空数组而不是删 key
- 任何超过 30 分钟的卡壳 → 立刻回报

完成后这个任务 + AE 副窗口的 5 mp4 落盘 + 主对话改 paths.ts 5 行 null → staticFile = 整片 AE 段最终样。
