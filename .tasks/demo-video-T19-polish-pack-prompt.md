# T19 — 收尾 Polish Pack（BGM + ~~SFX~~ + SRT + 响度 + 压缩 + 封面）

> **⚠️ 2026-05-12 导演修订**：
> - **Task 2「SFX 音效」整段跳过**。导演决定整片不加额外 SFX，只保留 Intro 的 AE Logo Reveal 自带的品牌 sting（已嵌入 AE 渲染产物）。理由：画面动效已经够叙事，再加 SFX 会过载。
> - 因此 Task 3「Remotion 集成」只需挂 BGM，不需要 SfxCue / audio-cues.ts
> - 第 11 节「导演关切点」中关于 SFX 的部分作废
> - 工时从 6-7h 降到 **4-5h**
>
> **⚠️ 顺序约束**：本任务必须在 **T20（导演 Round-2 修订）完成且 Remotion 重渲后**才开始，否则字幕架构变动会让 SRT 导出失效、响度归一化重做。

> **角色**：你是资深产品宣传片后期 + 混音 + 打包工程师，给医小管 4 分钟演示视频做最后一公里。
> **导演意图**：T17/T18 产出的是"视觉修订清单"，T19 是把**听觉、字幕、工程交付、封面**全收尾，让片子从"能看"变"能发布"。
> **哲学**：**克制比堆砌难十倍**。BGM 宁低勿高，封面宁简勿花。每一个元素问自己 3 遍"真的需要吗"。

---

## 0. 输入与现状

### 主视频
- `.tmp/demo-video/remotion-final/out/final-fast.mp4`（4min @1080p30，当前版本）
- 结构唯一真理源：`.tmp/demo-video/remotion-final/src/data/sections.ts`
- 字幕真理源：`.tmp/demo-video/remotion-final/src/data/captions.ts`

### 段落时间速查（从 sections.ts 读取实际值后回填到此表）
| 段 | 起（秒） | 止（秒） | 内容 | SFX 候选点 |
|---|---|---|---|---|
| Intro | 0 | ~15 | Logo Reveal + 标语 | Logo 出现 sting、whoosh 收尾 |
| AE 概念 | ~15 | ~65 | 5 个 AE 场景 | 场景切换 whoosh ×4 |
| D1 学生 | ~65 | ~135 | 提问 → AI 流答 → 转人工 | send pop、typing tick、escalate ding |
| D2 教师 | ~135 | ~185 | 工作台 → 看板 → 知识库 | 无（AE→D2 切换有 whoosh 即可，内部保持安静） |
| D3 双端 | ~185 | ~225 | 左右同屏实时 | send pop、receive soft chime（学生/教师各一次足矣） |
| Outro | ~225 | ~240 | 品牌收尾 | Logo closing sting |

**SFX 总数上限：15 个**（若实际加到 20+，删到 15）

### 依赖资产现状
- 旁白 MP3：`.tmp/demo-video/voice/*.mp3`（5 段）
- Logo：`.tmp/demo-video/brand/logo.png`（如果存在）
- AE Logo Reveal：`.tmp/demo-video/ae-scenes/logo-reveal.mp4`

---

## 1. 任务拆解（6 件事，按依赖顺序）

```
┌─────────────┐
│ 1. BGM 选型 │──┐
└─────────────┘  │
┌─────────────┐  ├──▶┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 2. SFX 选配 │──┘   │ 3. Remotion  │──▶│ 4. 响度归一化│──▶│ 5. H264 二压 │
└─────────────┘      │    集成      │   │  EBU R128    │   │   < 80MB     │
                     └──────────────┘   └──────────────┘   └──────────────┘
┌─────────────┐                                                     │
│ 6. SRT 导出 │── 独立，可任意并行                                   │
└─────────────┘                                                     │
┌─────────────┐                                                     ▼
│ 7. 封面图   │── 独立，可任意并行                           ┌──────────────┐
└─────────────┘                                              │ 最终交付     │
                                                             └──────────────┘
```

---

## 2. Task 1: BGM 选型（科技风 × 医疗温度）

### 2.1 风格规范（导演钦点）
- **大方向**：**科技风**，但**不要赛博朋克/EDM 硬核**
- **子风格**：ambient tech / modern corporate / uplifting synth / minimal techno（细分）
- **情绪**：专业（稳）+ 温暖（医疗）+ 向上（希望），避免冷峻、压抑、夜店感
- **节拍**：80-110 BPM，中低密度，不要疯狂鼓组
- **乐器**：合成器 pad / piano / 柔和 arpeggio / 轻电子鼓，**禁止**失真吉他、大号铜管、808 trap
- **结构偏好**：有 intro（0-30s 轻启）→ build（30-180s 主体）→ outro（180-240s 收尾）的 4 分钟整段最佳
- **长度容忍**：3:30-4:30 都行，不够就 loop + crossfade 自补

### 2.2 资源优先级
1. **Pixabay Music**（CC0，无水印，直接下）—— 首选
2. **YouTube Audio Library**（No copyright，商用 OK）
3. **Uppbeat.io**（免费档有限制，注意 attribution）
4. **Freesound.org**（CC，筛选 license）
5. **Artlist / Epidemic Sound**（订阅付费，如果预算允许质量最高）
6. **Suno AI v4 自生成**（如果前面都不满意，用 prompt 生成，生成 3-5 版选最好的）

### 2.3 工作流
```
1. 用关键词搜：
   - "ambient tech corporate"
   - "medical technology uplifting"  
   - "minimal electronic inspiration"
   - "future healthcare background"
   - "soft tech piano synth"
   
2. 下载 10 个候选到 .tmp/demo-video/bgm-candidates/
   命名：01-<source>-<title>.mp3

3. 用 ffprobe 拿长度/比特率/响度，写 bgm-candidates.json
   {
     "file": "01-pixabay-tech-uplift.mp3",
     "duration": 215,
     "bpm_estimate": 92,
     "lufs": -14.2,
     "license": "Pixabay free",
     "url": "https://...",
     "notes": "钢琴+pad，intro 轻，中段 build 合适"
   }

4. 按导演标准打分 (1-10)，选 top 3 写到 bgm-report.md

5. 把 TOP 1 复制到 .tmp/demo-video/remotion-final/public/bgm/main.mp3
   TOP 2-3 存 public/bgm/alt-{2,3}.mp3 作备用
```

### 2.4 验收
- `bgm-candidates.json` 含 10 个候选
- `bgm-report.md` 含 top 3 推荐 + 选中理由 + 备选切换成本评估
- `public/bgm/main.mp3` 就绪可被 Remotion 引用

---

## 3. Task 2: SFX 音效选配（关键 beat only）

### 3.1 反做作宪法（导演强制纪律）
1. **总数 ≤ 15**，超出必删
2. **禁止 UI 声音农场**：鼠标点击不是每次都有声
3. **禁止卡通化 SFX**：不要 "boing"、"pop!"、"whee" 这种
4. **每个 SFX < 800ms**（避免遮盖旁白）
5. **SFX 音量 -20 LUFS**（比 BGM -24 高 4dB，比旁白 -14 低 6dB）
6. **同类 SFX 复用同一文件**（4 个段切换 whoosh 用同一个 mp3，不要 4 个不同的）
7. **每段内部最多 3 个 SFX**，D1/D3 交互密集段可破例到 5 个，不能再多

### 3.2 SFX 分类与候选（15 个以内）

| # | 名称 | 用途 | 时长 | 出现次数 | 音色参考 |
|---|---|---|---|---|---|
| 1 | `logo-sting.mp3` | Intro Logo Reveal | 1-2s | 1 | 低频 thud + 高频 shimmer |
| 2 | `whoosh-transition.mp3` | 段切换 | 400-600ms | 4-5 | 空气扫过 + 轻微 reverb tail |
| 3 | `send-pop.mp3` | 学生发消息 | 80-150ms | 2-3 | 柔和 "tuc"，不要 bubble pop |
| 4 | `typing-tick.mp3` | AI 流式第一字 | 200ms | 1 | 细微机械/电子触感 |
| 5 | `escalate-ding.mp3` | 转人工触发 | 400-600ms | 1 | 温暖 chime，不要报警 |
| 6 | `receive-chime.mp3` | 教师消息到达 | 300-500ms | 1 | 柔和 UI notification |
| 7 | `outro-closing.mp3` | Outro 收尾 | 1-2s | 1 | 与 logo-sting 呼应但更收 |

### 3.3 资源优先级
1. **Mixkit**（免费，商用 OK，无 attribution）—— 首选 UI/科技类
2. **Pixabay Sound Effects**（CC0）
3. **Zapsplat**（免费要注册，质量高）
4. **Freesound**（CC，筛选 license）

搜索关键词：
- `ui notification soft tech`
- `whoosh transition modern`
- `message send pop subtle`
- `logo reveal sting tech`
- `chime notification warm`

### 3.4 工作流
```
1. 每类挑 3 个候选下载到 .tmp/demo-video/sfx-candidates/<category>/
2. 盲听 2 秒决定留不留（做作的直接删）
3. 每类选 1 个定稿，复制到 .tmp/demo-video/remotion-final/public/sfx/
4. 用 ffmpeg 批量归一化到 -20 LUFS：
   ffmpeg -i in.mp3 -af loudnorm=I=-20:TP=-2:LRA=7 out.mp3
5. 写 sfx-manifest.json 记录每个 SFX 的元信息
```

### 3.5 时间点精确对齐
在 `events.json`（D1/D2/D3 录制事件）里找精确 frame：
- `.tmp/demo-video/out/d1/events.json`
- `.tmp/demo-video/out/d2/events.json`  
- `.tmp/demo-video/out/d3/student/events.json`

用 event 的 `t`（相对录制起点 ms）+ sections.ts 里 D1/D2/D3 的起始帧，算出整片绝对帧：
```js
const absoluteFrame = Math.round(sectionStartFrame + (event.t / 1000) * 30)
```

---

## 4. Task 3: Remotion 集成（BGM + SFX + Ducking）

### 4.1 文件组织
```
.tmp/demo-video/remotion-final/
  public/
    bgm/main.mp3
    sfx/
      logo-sting.mp3
      whoosh-transition.mp3
      send-pop.mp3
      typing-tick.mp3
      escalate-ding.mp3
      receive-chime.mp3
      outro-closing.mp3
  src/
    data/
      audio-cues.ts        # ★ 新增：SFX 时间点清单
    components/
      BgmTrack.tsx         # ★ 新增：BGM + ducking 组件
      SfxCue.tsx           # ★ 新增：单个 SFX 组件
```

### 4.2 audio-cues.ts 结构
```ts
export type SfxCue = {
  id: string
  src: string          // relative to public/
  frame: number        // absolute frame in main composition
  volume?: number      // 0-1, default 0.5
  fadeIn?: number      // frames
  fadeOut?: number     // frames
}

export const SFX_CUES: SfxCue[] = [
  { id: 'intro-logo', src: 'sfx/logo-sting.mp3', frame: 30, volume: 0.6 },
  { id: 'ae-enter', src: 'sfx/whoosh-transition.mp3', frame: 450, volume: 0.5 },
  // ... 填满 15 个上限内的
]
```

### 4.3 BgmTrack.tsx 核心
- 用 `<Audio>` 挂 `public/bgm/main.mp3`，整片贯穿
- 基础音量 0.35（≈ -20 dB / -24 LUFS 区间）
- **旁白 ducking**：在旁白段（从 sections.ts + voice mp3 映射）用 Remotion `interpolate` 把音量降到 0.15（-4dB sidechain）
- 公式：
  ```tsx
  const voiceActive = isInVoiceSegment(frame)
  const volume = voiceActive ? 0.15 : 0.35
  ```

### 4.4 SfxCue.tsx 核心
```tsx
export const SfxCue: React.FC<{cue: SfxCue}> = ({cue}) => (
  <Sequence from={cue.frame} durationInFrames={90 /* ~3s 最多 */}>
    <Audio
      src={staticFile(cue.src)}
      volume={cue.volume ?? 0.5}
      // 可选淡入淡出
    />
  </Sequence>
)
```

### 4.5 挂载到主 Composition
在 `Composition.tsx` 的根 `<AbsoluteFill>` 里加：
```tsx
<BgmTrack />
{SFX_CUES.map(cue => <SfxCue key={cue.id} cue={cue} />)}
```

### 4.6 验收
- 本地 `npx remotion studio` 播放，耳朵盲听确认：
  - BGM 在旁白段明显退后
  - SFX 在段切换 + 关键 beat 点缀自然
  - 无刺耳、无抢戏、无做作
- 没有任何一个 SFX 让你"想关掉"

---

## 5. Task 4: SRT 字幕导出（双语可选）

### 5.1 数据来源
`.tmp/demo-video/remotion-final/src/data/captions.ts`

### 5.2 导出脚本
`.tmp/demo-video/export-srt.mjs`：
- 读 captions.ts（用 `tsx` 或者直接解析）
- 每条 caption 转成：
  ```
  1
  00:00:03,500 --> 00:00:07,200
  用 AI + 老师，建一座医学院的知识桥
  ```
- 关键转换：frame → `HH:MM:SS,mmm`：
  ```js
  const framesToSrt = (frame, fps = 30) => {
    const ms = Math.round((frame / fps) * 1000)
    const h = Math.floor(ms / 3600000)
    const m = Math.floor((ms % 3600000) / 60000)
    const s = Math.floor((ms % 60000) / 1000)
    const rem = ms % 1000
    return `${pad2(h)}:${pad2(m)}:${pad2(s)},${pad3(rem)}`
  }
  ```
- 输出：
  - `.tmp/demo-video/remotion-final/out/final.zh.srt`（主输出）
  - `.tmp/demo-video/remotion-final/out/final.en.srt`（可选，机器翻译占位）

### 5.3 双语翻译（可选，如果时间够）
- 用 Gemini / Qwen / 翻译 API 把 zh → en
- 医学专有名词不翻：医小管 → "Yixiaoguan"，不要变"Little Tube"
- 输出 `final.en.srt`，导演人工 10 分钟过一遍

### 5.4 验收
- `final.zh.srt` 打开用 VLC 播主视频，字幕时间对齐误差 < 200ms
- 无缺失行、无时间重叠

---

## 6. Task 5: 响度归一化（EBU R128，两轨 mix 前）

### 6.1 为什么要做
- 旁白、BGM、SFX 三轨来源不同，响度差异可能 > 10 LU
- 直接 mix 会出现：旁白段震耳 / SFX 段压不住 / BGM 段莫名大声
- 标准：广播/流媒体通用 **EBU R128** → integrated -16 LUFS, TP -1.5 dBTP, LRA ≤ 11 LU

### 6.2 工作流（分轨归一化，mix 后再做一次整体归一化）
```bash
# 旁白：-14 LUFS（比主基准高 2dB，保清晰）
ffmpeg -i voice/raw.mp3 -af loudnorm=I=-14:TP=-1.5:LRA=7:print_format=summary voice/normalized.mp3

# BGM：-24 LUFS（低垫底）
ffmpeg -i bgm/raw.mp3 -af loudnorm=I=-24:TP=-2:LRA=7 bgm/normalized.mp3

# SFX 批量：-20 LUFS
for f in sfx/*.mp3; do
  ffmpeg -i "$f" -af loudnorm=I=-20:TP=-2:LRA=7 "sfx_norm/$(basename $f)"
done
```

### 6.3 Remotion 渲染后整体归一化
Remotion 输出 `final-fast.mp4` 后：
```bash
# 两遍 loudnorm（推荐）
# Pass 1：测量
ffmpeg -i final-fast.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2> loudnorm-pass1.log

# 提取 measured_* 参数填入 Pass 2
ffmpeg -i final-fast.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=XXX:measured_TP=XXX:measured_LRA=XXX:measured_thresh=XXX:offset=XXX:linear=true:print_format=summary" -c:v copy -c:a aac -b:a 192k final-normalized.mp4
```

### 6.4 验收
- `ffmpeg -i final-normalized.mp4 -af ebur128=peak=true -f null -` 输出 integrated 在 -16 ± 0.5 LUFS
- TP ≤ -1.0 dBTP

---

## 7. Task 6: H264 最终压缩（< 80MB）

### 7.1 目标参数
- 分辨率：1920×1080 保持
- 帧率：30 保持
- 视频编码：libx264
- 音频：AAC 192k
- 容器：mp4
- **文件上限 80MB**

### 7.2 命令
```bash
# 如果 final-normalized.mp4 已经 < 80MB，直接 copy 流量
# 否则 CRF + preset slow 二压：

ffmpeg -i final-normalized.mp4 \
  -c:v libx264 -preset slow -crf 22 \
  -c:a aac -b:a 192k -ac 2 \
  -movflags +faststart \
  -pix_fmt yuv420p \
  final-release.mp4

# 如果 CRF 22 还超 80MB，逐步上调 CRF 到 24、26
# 但不要超过 26，画质会明显糊
```

### 7.3 验收
- 大小 ≤ 80MB
- 用 VLC / QuickTime / Chrome 均可播放
- `ffprobe final-release.mp4` 看到：1920×1080, 30fps, yuv420p, aac 192k

---

## 8. Task 7: 封面图（1920×1080 静态海报）

### 8.1 三条路线任选（优先 A）

**路线 A：Remotion 单帧渲染（推荐）**
- 在 `src/` 里新建 `src/Cover.tsx`，一个静态海报组件
- 用已有的 LightBackdrop + Logo + 标语"医小管 · 用 AI + 老师建一座医学院的知识桥"
- `npx remotion still --frame=0 src/Cover.tsx out/cover.png`
- 优点：跟视频品牌完全一致，字体/颜色/布局延续 tokens

**路线 B：视频关键帧抽取 + 加工**
- 从 final-release.mp4 的 Intro Logo Reveal 高光帧截图
- 用 Photoshop / Figma 加标题覆盖
- 缺点：人工

**路线 C：Midjourney / AI 生成**
- prompt: "modern medical app poster, purple gradient, clean typography, minimalist, 1920x1080"
- 缺点：品牌一致性差

### 8.2 产物
`.tmp/demo-video/remotion-final/out/cover.png`（≤ 2MB，jpg 也行）

---

## 9. 交付物清单（全任务完成后）

```
.tmp/demo-video/remotion-final/out/
  final-release.mp4          # 最终视频，≤ 80MB
  final.zh.srt               # 中文字幕
  final.en.srt               # 英文字幕（可选）
  cover.png                  # 封面图
  loudness-report.txt        # 响度测量报告
  
.tmp/demo-video/
  bgm-candidates/            # 10 个 BGM 候选
  bgm-candidates.json
  bgm-report.md              # BGM 选型报告
  sfx-candidates/            # 分类的 SFX 候选
  sfx-manifest.json
  polish-report.md           # T19 总体交付报告
```

---

## 10. 执行顺序与时间预估

| 步 | 任务 | 依赖 | 预估 |
|---|---|---|---|
| 1 | BGM 选型 | 无 | 1.5h |
| 2 | SFX 选配 | 无 | 1.5h |
| 3 | SRT 导出 | captions.ts 已定 | 0.5h |
| 4 | 封面图 | 无 | 0.5-1h |
| 5 | Remotion 集成 BGM+SFX | 1+2 | 1h |
| 6 | 各轨响度归一化 | 5 | 0.5h |
| 7 | 重渲 Remotion | 6 | 0.5h（取决于渲染机） |
| 8 | 整体响度归一化 + H264 二压 | 7 | 0.5h |
| 9 | 验收 + 报告 | all | 0.5h |

**总计 ≈ 6-7h**，可并行把 1/2/3/4 一起开，压到 4-5h。

---

## 11. 导演关切点（强制复读）

- ❌ **不要 SFX 声音农场**：总数 ≤ 15，同类复用
- ❌ **不要 BGM 抢戏**：旁白段 ducking 必做
- ❌ **不要做作 BGM**：避免 EDM/赛博朋克，要 ambient tech + 医疗温暖
- ❌ **不要不对齐字幕**：SRT 误差 < 200ms
- ❌ **不要 > 80MB**：CRF 上调到 24 也行，别破 80
- ✅ **克制 >> 堆砌**：每个元素问 3 遍"真的需要吗"

---

## 12. 完成回报格式

```
T19 完成 ✅
- BGM: <title>（<source>，<license>）
- SFX: N 个（种类：段切 / 交互 / Logo sting / Outro）
- 旁白响度: -14.X LUFS
- BGM 响度: -24.X LUFS  
- 整体响度: -16.X LUFS integrated, -1.X dBTP
- SRT: final.zh.srt (N 条) / final.en.srt (N 条，机译未审)
- 封面: cover.png (路线 A/B/C)
- 最终文件: final-release.mp4 (XX MB)
- 报告: .tmp/demo-video/polish-report.md
- 总用时: X.Xh
```

— END —
