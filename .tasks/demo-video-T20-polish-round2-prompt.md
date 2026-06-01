# T20 — 导演 Round-2 修订（缩放收敛 + AE 尾延 + 字幕架构重构）

> **角色**：你是产品演示视频的视觉工程师 + 字幕架构师。
> **背景**：T15（电影感）+ T16（Screen Studio）已落地，导演看完整片认为**整体跑通、细节翻车**。本轮针对 3 个具体问题做精准修订，不要扩散范围。
> **核心哲学**：**Less is more**。这一轮的所有修改都在做减法或重新组织，**不要新增动效、不要新增层次**。

---

## 0. 导演 Round-2 反馈原文（必读）

> 1. 它这一版的缩放或者说特效用的太多了。其实只有几个地方需要做缩放的，比如点击按钮、流式传输这种比较有特点的地方。反而像是整体概览、界面展示、滑屏，反倒是不适合缩放的。
> 
> 2. AE 视频嵌入的那个地方最后一节画面有一点裁切了，估计是按照字幕来的。我觉得把话说完的停顿拉长一点应该就够了，因为不差几秒。
> 
> 3. 比较严重或者说影响比较大的字幕问题：目前画面下方放的是主题或者说标记，我觉得可以稍微调整一下——变成大字放到画面两侧，再加一些小字点缀一下，接着就可以把字幕放上去了，就跟我们之前说的一样：叠加一个边缘化的毛玻璃底，加上字幕，效果应该会很不错。

---

## 1. Task A — 缩放/特效收敛（优先级最高）

### 1.1 问题诊断
当前 D1/D2/D3 段大量使用 zoom-in 效果，**误用在了静态浏览/滑屏/整体概览的画面上**。Screen Studio 真正的心法是：

| 场景类型 | 是否缩放 | 原因 |
|---|---|---|
| ✅ 点击按钮瞬间 | YES，急速 zoom 到点击点 ±150px，停留 300-500ms 再 zoom out | 强化"我在做这个动作" |
| ✅ AI 流式回答首字出现 | YES，缓慢 zoom in 到 1.15× 然后 hold | 强化"内容正在生成"的紧张感 |
| ✅ 实时消息到达瞬间（D3 教师收到学生消息） | YES，对消息气泡做 1.2× pulse | 强化"实时双向"的核心卖点 |
| ❌ 整体概览（如 dashboard 一进入就 zoom in） | NO，保持 1.0× | 用户需要扫视全局，缩放反而让眼睛找不到锚点 |
| ❌ 界面展示（teacher 工作台、知识库列表） | NO，静止 | 同上 |
| ❌ 滑屏/滚动 | NO，画面已有动 | 再缩放就过载 |

### 1.2 工程改动

1. **找出所有当前的 zoom 触发点**
   - `grep -r "interpolate.*scale\|zoom\|transform.*scale" .tmp/demo-video/remotion-final/src/sections/`
   - 把每一处归类到上面表格里

2. **删除三种"该静止的"缩放**
   - dashboard 进入时的 zoom — 删
   - 列表/概览的 zoom — 删
   - 滑屏配合的 zoom — 删

3. **保留并优化三种"该缩放的"**
   - 点击按钮：参考 `events.json` 里 `tap` 事件的 `x/y`，做精准的"哪点击哪 zoom"，不要全画面缩放
   - 流式输出：D1 段 AI 回答出现的那一帧，对回答容器做 1.0→1.15× 的缓慢 spring
   - 实时消息到达：D3 段教师收到的消息气泡 1.0→1.2× pulse 后回到 1.05×（保留轻微 emphasis）

4. **新增"克制度自检"**
   - 整片缩放总次数 ≤ **8 次**
   - 任何缩放持续时长 ≤ 1.5s（不要"长 zoom 摄影机感"）
   - 同段内连续缩放间隔 ≥ 3s（避免眩晕）

### 1.3 验收
- 看 D2 教师段：整段不应有任何缩放（教师工作台是浏览场景）
- 看 D1 学生段：只在"点发送按钮""AI 流式输出""转人工触发" 三处有缩放
- 看 D3 双端：只在"消息发出""消息到达对端" 处有缩放
- 全片 zoom 次数 ≤ 8，每次 ≤ 1.5s

---

## 2. Task B — AE 段尾延长（最简单）

### 2.1 问题
`sections.ts` 里 AE 段当前 `durationSec: 34`，AE 渲染输出的 5 个 scene 的字幕在 30s 后才念完，导致最后一节"话还在收尾，画面已经切到 D1"。

### 2.2 修复
1. 看 AE 渲染产物的实际时长：
   ```powershell
   ffprobe -v error -show_entries format=duration .tmp/demo-video/ae-scenes/ae-final.mp4
   ```
2. 在 `.tmp/demo-video/remotion-final/src/data/sections.ts` 把 AE 段的 `durationSec` 从 `34` 调到 **`38` 或 `40`**（多 4-6s 缓冲）
3. 注意 AE 段后面的所有段 `fromFrame` 都会因为累加自动后移，**总片长会从 240s 变成 244s 或 246s**——这是预期，不要硬保 240
4. 如果旁白音轨在某段是写死偏移的（比如 D1 旁白文件里的某句假设了 105s 是开始位置），跟着调整偏移；如果是按段相对偏移就不用动

### 2.3 验收
- AE 最后一节字幕念完后还有 ≥ 1.5s 视觉停顿才切到 D1
- 整体节奏不会显得拖沓（4-6s 的延长在整片里几乎察觉不到）

---

## 3. Task C — 字幕架构重构（工作量最大，效果最显著）

### 3.1 当前问题
当前所有字幕（包括叙事字幕、段标识/装饰文本）都堆在底部 pill 里，层次扁平、易读性差、毛玻璃感"白底飘在白底上"看不出来。

### 3.2 目标架构（导演钦点）

```
┌─────────────────────────────────────────────────┐
│                                                  │
│  大字           [视频/截图主体]          大字    │  ← Layer 1: 两侧大字（氛围/主题）
│  小字                                    小字    │  ← Layer 2: 小字点缀
│                                                  │
│                                                  │
│         ┌────────────────────────┐              │
│         │  ▓ 毛玻璃 pill ▓ 字幕  │              │  ← Layer 3: 底部主字幕
│         └────────────────────────┘              │
└─────────────────────────────────────────────────┘
```

### 3.3 三层各自的设计规范

#### Layer 1：两侧大字（氛围/主题）
- **位置**：画面左右两侧，距边缘 80-120px，垂直中线偏上 1/3 处
- **字号**：120-180px（hero size）
- **字重**：800（Black）
- **颜色**：当前页面主题色的 30-40% alpha（半透明，融入背景，不抢戏）
- **内容来源** ⭐ 关键决定：

  **方案 A（导演倾向）**：每段 **2 个关键词**，左右各一
  - Intro：左 "AI" 右 "桥梁"
  - AE：左 "知识" 右 "工程"
  - D1：左 "提问" 右 "流答"
  - D2：左 "教学" 右 "数据"
  - D3：左 "实时" 右 "双向"
  - Outro：左 "医小管" 右 "服务全程"

  **方案 B**：段标题 + 段索引（"D1 学生端 · 70秒"，左字"01"右字"学生"）

  **方案 C**：旁白高光词，每 5-10s 替换一次（动态最强但复杂度也最高）

  → **若不确定，先做 A 方案，效果不满意再升级到 C**

- **动效**：
  - 段进入时左右大字分别从屏幕外滑入（左字从左滑入右字从右滑入），spring damping=20
  - 段切换时不滑出，直接跟段一起 fade out
  - 关键词替换时（方案 C）用字符级 stagger fade

#### Layer 2：小字点缀
- **位置**：紧贴 Layer 1 大字下方（左侧大字下方放左侧小字）
- **字号**：18-22px
- **字重**：400 或 500
- **颜色**：当前页面主题色 50% alpha
- **内容**：
  - 段索引/段标题（如 `01 / Intro` `02 / AE`）
  - 或时间戳（如 `00:13` `00:47`）
  - 或英文 tagline（如 `AI + Mentor`、`Knowledge as Service`）
- **作用**：给大字一个"语义脚注"，提升专业感

#### Layer 3：底部主字幕（毛玻璃 pill）
- **位置**：画面下方，距底边 80px
- **字号**：38-44px（normal narrative）
- **字重**：500-600
- **颜色**：白色或近白
- **背景 pill**：
  ```css
  background: rgba(255, 255, 255, 0.08);   // 极低 alpha，不"压"画面
  backdrop-filter: blur(28px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;                    // 完全圆角
  padding: 12px 28px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.4);
  ```
- **关键 — 边缘化**：pill 的 `mask` 用径向渐变，让 pill 中央实而边缘虚，自然消融在画面里：
  ```css
  mask-image: radial-gradient(ellipse, black 60%, transparent 100%);
  ```
  这个就是导演说的"边缘化的毛玻璃底"。
- **动效**：保留当前 spring 动画，但改成 character-level fade-in（不要整条 pill 一起跳出来，跳得太硬）

### 3.4 工程改动

**文件级动作**：

1. `src/data/captions.ts` 扩展 schema
   ```ts
   export type CaptionType = 
     | "narrative"       // Layer 3 主字幕（叙事）
     | "atmosphere_left" // Layer 1 左侧大字
     | "atmosphere_right"// Layer 1 右侧大字  
     | "footnote_left"   // Layer 2 左侧小字
     | "footnote_right"; // Layer 2 右侧小字
   
   export type Caption = {
     section: SectionId;
     type: CaptionType;
     text: string;
     fromSec: number;
     durationSec: number;
     // ... 其他原字段
   }
   ```

2. `src/components/Captions.tsx` 拆成 3 个子组件
   - `NarrativeCaption.tsx` — Layer 3 主字幕（接管现有 pill 实现，加边缘化 mask）
   - `AtmosphereText.tsx` — Layer 1 两侧大字
   - `FootnoteText.tsx` — Layer 2 两侧小字
   - `Captions.tsx` 变成纯路由，按 type 分发到子组件

3. 各 Section（IntroSection / D1StudentSection / ...）保持不动，因为 captions.ts 是数据驱动的；改 captions 数据 + Captions 组件即可全片生效

### 3.5 验收（毛玻璃感的"是否高级"判断）
- 暂停在任意 D1/D2 帧：
  - ✅ 两侧大字看起来像"环境装饰"，不抢戏，但能在余光看到主题
  - ✅ 小字像专业杂志的脚注，给大字"接地气"
  - ✅ 底部 pill 边缘消融到背景里，**绝对不能看到一个"白色长方块"漂浮在画面上**
- 反例（必须避免）：
  - ❌ 两侧大字太实，像水印
  - ❌ pill 边缘是硬切的圆角矩形
  - ❌ 字幕动效"哒"地一下整条跳出来

---

## 4. 工作流程建议（避免 20min 渲染阻塞）

1. **开发循环用 `remotion studio`**（`npm run dev`），不要用 `npm run render`
2. 改字幕组件 → 浏览器热重载 → 拖时间线到任意段头看效果
3. 觉得够 polish 时用 `render --scale=0.5` 出半分辨率 draft 验证整体（3-5min）
4. 全片定稿才用 `render --concurrency=auto` 出 1080p 终版

---

## 5. 不在本任务范围（强制约束）

以下属于其他任务，**不要碰**：
- ❌ BGM 选择和挂载（→ T19）
- ❌ SFX 音效（导演决定不加，整片只保留 AE Logo Reveal 自带的）
- ❌ 任何新增动效或转场效果（这一轮是减法，不是加法）
- ❌ 修改 D1/D2/D3 录制 webm（已 frozen）
- ❌ 修改 AE 渲染产物（已 frozen）

---

## 6. 完成回报格式

```
T20 完成 ✅

A. 缩放收敛
- 删除的"误用缩放": N 处（dashboard/列表/滑屏）
- 保留+优化的"对的缩放": N 处（点击/流答/实时消息）
- 整片 zoom 总次数: N（≤ 8）

B. AE 段尾延长
- AE durationSec: 34 → XX
- 整片总长: 240s → XXs
- 旁白偏移调整: 是/否

C. 字幕架构重构
- captions.ts 新增 atmosphere/footnote 数据: N 条
- 新组件: AtmosphereText.tsx, FootnoteText.tsx
- pill 边缘化 mask: 已实现/未实现
- 主题词方案: A/B/C
- Studio 预览截图: .tasks/demo-video-T20-preview/{intro,ae,d1,d2,d3,outro}.png

draft 渲染: out/draft-t20.mp4（半分辨率，作为整体效果存档）
```

— END —
