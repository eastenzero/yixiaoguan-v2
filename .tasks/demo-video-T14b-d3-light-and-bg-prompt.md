# 副窗口任务 · T14b D3 浅色背景 + Intro/Outro 自画背景动画

> 2026-05-12 凌晨 主对话导演反馈
> 上一轮（T14）：Remotion 骨架完成，整片 4:00 已能渲，配音字幕全集成 ✅
> 本轮：用户实看后定位 D3 段背景与整片调性割裂 + Intro/Outro 也要从深色转浅色

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\remotion-final\
```

---

## Bug 1 · D3 段背景全黑 → 改浅色

### 现象

D3 双端实时分屏段（整片 02:32-03:22, 即 D3 段内 0-50s）整段**黑底**。学生 webm + 教师 webm 之间的中央区域、两侧 padding、顶部 / 底部空白都是黑色 #000 或近黑色。

### 视频证据

`out/final-fast.mp4` D3 段任意一帧：手机两端 webm 浮在黑底上，跟整片基调（紫粒子 / 浅紫白 / Outro 也偏深）严重不和谐。

### 期望

D3 段改成**浅色调**，跟 AE 段保持一致或相近：
- AE 段已有的设计令牌 `bgGradientTop` / `bgGradientBottom`（参考 `src/styles/tokens.ts`）已经是浅色渐变
- D3 段可以用同一对令牌、或微调出独立但统调的浅色

中央区域（学生 webm 和 教师 webm 之间，目前用来画"光线 Beam" + "← 学生 / 教师 →" 标签）需要确保**在浅色底下文字依然可读**，可能要把字色从亮色改深紫 `#5B21B6` 或类似。

### 决策（导演方向）

- ✅ D3 背景**必须**改浅色，跟 AE 统调
- ✅ Beam 光效保留（但颜色需调到浅底也能看见）
- ✅ "← 学生 / 教师 →" 标签字色调到浅底可读
- ❌ 不要改 D3 段的视频对齐逻辑（`D3_START_FROM_FRAMES = 337` 不动）
- ❌ 不要改 D3 段时长（保持 50s）
- ❌ 不要改字幕内容 / 位置

---

## Bug 2 · Intro / Outro 转场背景偏深 → 自画浅色动画

### 现象

- **Intro 13s**：当前用 Pexels 紫粒子 stock mp4（`intro-candidates/01-pexels-...`）作为背景，紫粒子整体偏深，跟"医小管"品牌字 fade in 时形成"深底浮亮字"对比 —— 用户认为跟整片浅色基调不统一
- **Outro 18s**：当前用占位（紫底 + slogan 字幕），同样偏深

### 用户决策

> "logo 那边我可以处理 就不用你们专门来做了 如果背景你们可以自己画的话就更好 如果画不了 我去找视频也是 OK 的 只要不太喧宾夺主 我觉得应该自己画也是 OK 的"

→ **Intro / Outro 背景动画由你（opencode）评估**：

**选项 A**（推荐）：用 React + CSS / SVG / Remotion 内置 spring / interpolate **自己画**一个浅色调的流动 / 渐变 / 粒子 / 光晕动画。要求：
- 浅色调，跟 AE/D3 统一（参考 `tokens.bgGradientTop/Bottom`）
- 不抢字幕戏（饱和度 / 透明度低，作为背景层）
- 有动感不死板（spring 弹性 / 周期渐变 / Bezier 路径 / 等）
- 风格倾向：Lo-fi corporate inspirational / 苹果发布会的"浅紫白光晕缓慢呼吸"那种调性

**选项 B**：评估后认为自画效果不行 → 把 Intro / Outro 背景**留占位**（白底 + 简单 fade），等用户找浅色 stock 视频。在 README.md 里写明替换路径约定即可。

### 不要做的事

- ❌ 不要保留当前的 Pexels 紫粒子 stock 在 Intro 段（如果选 A：自画替换；如果选 B：白底占位等用户）
- ❌ 不要保留 Outro 紫底（同上，要么自画浅色，要么白底占位）
- ❌ 不要改 Intro / Outro 字幕内容（"医小管" + slogan 不动）
- ❌ 不要改 Intro / Outro 段时长（13s / 18s 不动）
- ❌ 不要改 Logo（用户自处理）

---

## 你的实现自由度

主对话**只描述现象 + 决策方向，不指定技术方案**。怎么实现取决于你：
- D3 浅色：可以改单个组件、可以改 token、可以改 Composition root，自己定
- Intro / Outro 背景动画：选 A 自画就放手画，选 B 留占位就清晰留接口
- Beam 光效在浅底的颜色：紫色基调即可（`#7C3AED` 主色 / `#5B21B6` 深紫 / `#A78BFA` 浅紫，自己挑）

主对话信任你的审美。

---

## 验收清单

主对话验收会做：

### D3 浅色
- 重渲 `out/final-fast.mp4`，跳到 D3 段任意一帧
- 背景为浅色（不能是 `#000` / `#1A1A2E` 等深色）
- 中央 Beam 光效在浅底依然有视觉吸引力
- "← 学生 / 教师 →" 标签字号 / 字色清晰可读
- 字幕 "实时推送 · WebSocket" / "Centrifugo 频道" / "端到端 < 200ms" / "对话 · 流畅 · 端到端" 在浅底依然清晰

### Intro / Outro 背景
- 重渲后跳到 0-13s 看 Intro，跳到 222-240s 看 Outro
- 整体调性跟 AE/D1/D2/D3 统一（浅色为主）
- 不喧宾夺主（字幕仍是视觉焦点）
- 如选 B 留占位：README.md 明确写出"Intro 背景待用户填充：替换 `xxx.tsx` 第 N 行 / 替换 `paths.ts` `introBg` 为新路径"

### 通用
- `npm run render` 一次过
- 总时长仍精确 240.02s
- 段时长不变（13/34/65/60/50/18）
- 配音对齐不变
- 字幕对齐不变

跑完了告诉主对话：
1. D3 背景改成什么色（color hex 或 gradient 配置）
2. Intro / Outro 选了 A（自画）还是 B（占位）
3. 如选 A：用了什么技术（CSS gradient / SVG path animation / Remotion `<Sequence>` 嵌套 / `interpolate` 等），简要描述
4. 如选 B：占位实现 + 用户后期替换路径
5. 重渲后 mp4 路径 + 文件大小 + 渲染耗时
6. 你认为还有哪些视觉点位主对话应该看一眼

---

## 卡壳怎么办

- 浅色背景 + 学生 webm 边缘融化（webm 本身就是浅紫白） → 加投影 / 边框 / outer glow，自己 trade-off
- D3 Beam 在浅底完全看不见（白色 beam in white bg） → 换深紫 / 加发光 halo / 加描边
- Intro 自画的动画看着像 PowerPoint Smart Art → 退回选项 B 占位，不丢人
- Remotion `interpolate` / `Easing` API 不熟 → 主对话 memory 里没有相关 cheat sheet，自己看官方文档 https://www.remotion.dev/docs/animating-properties
- 任何超 90 分钟卡壳 → 立刻回报
