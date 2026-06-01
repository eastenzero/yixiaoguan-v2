# T18 — 多模态 AI 视觉审片（Gemini 3.1 Pro + Qwen3-VL 交叉验证）

> **角色**：你是被导演（人类用户）派来给医小管演示视频做 AI 视觉审片的工程师 + 评审顾问。
> **导演意图**：用 2026 年当下最强的视觉多模态模型，对刚剪好的 4 分钟 demo 视频做一次"严苛、可执行、带时间戳"的审片，输出结构化魔搭社区反馈，指导下一轮 polish。
> **硬性禁令**：**禁止 ffmpeg 抽帧路线**。必须用模型的**原生视频 input** 能力。抽帧会丢运动、节奏、字幕动效信息，正是这次审片的核心。

---

## 0. 大背景（必读，5 分钟）

这是医小管（医学院助手 App）的 4 分钟产品演示视频，结构如下（**唯一真理源**：`.tmp/demo-video/remotion-final/src/data/sections.ts`）：

| 序 | 段          | 时长 | 内容                                                         |
| -- | ----------- | ---- | ------------------------------------------------------------ |
| 1  | Intro       | ~15s | Logo Reveal（AE 渲染）+ 品牌口号                             |
| 2  | AE 概念段   | ~50s | 5 个 AE 场景（S23/S11/S18/S27/S30），4K 渲染，字幕嵌在 AE 里 |
| 3  | D1 学生端   | ~70s | Playwright 录的真机演示：提问 → AI 流式回答 → 转人工       |
| 4  | D2 教师端   | ~50s | 教师工作台 → 看板 → 知识库                                 |
| 5  | D3 双端实时 | ~40s | 同屏左右双手机：学生发 / 教师回 实时同步                     |
| 6  | Outro       | ~15s | 品牌收尾，标语 "医小管"                                      |

**当前状态**：T15（电影感）、T16（Screen Studio 感）已 done，本次审片是为 T17/T19 polish 提供数据驱动的修复清单。

**已知的导演关切点**（必须重点审）：

1. 字幕"玻璃感"是否到位 —— 之前白底太死板，最近一轮加了 `backdropFilter: blur(20px)` 但还想要更通透更高级
2. Screen Studio 风格的动态 zoom / pan / 鼠标光标 / 点击波纹是否自然，有没有"做作"或"机器感"
3. 转场是否电影感，还是廉价（突变、生硬、white flash 太重？）
4. AE 段和 Remotion 段的视觉一致性（光影、色温、字体）
5. 整体节奏：哪段冗长拖沓、哪段信息密度过高
6. 品牌呈现：logo reveal 是否震撼、outro 是否收得住

---

## 1. 输入资产清单

| 资产        | 路径                                                           | 用途               |
| ----------- | -------------------------------------------------------------- | ------------------ |
| 主视频      | `.tmp/demo-video/remotion-final/out/final-fast.mp4`          | **审片主体** |
| 剧本与节奏  | `video/04-script-plan.md`                                    | 段落意图           |
| 旁白文案    | `video/07-narration-script.md`, `video/08-narration-v2.md` | 旁白对齐           |
| 时间结构    | `.tmp/demo-video/remotion-final/src/data/sections.ts`        | 各段起止帧         |
| 字幕数据    | `.tmp/demo-video/remotion-final/src/data/captions.ts`        | 字幕时间码         |
| 字幕组件    | `.tmp/demo-video/remotion-final/src/components/Captions.tsx` | 玻璃感样式实现     |
| AE 渲染报告 | `.tasks/ae-theme/ae-full-delivery-report.md`                 | AE 段背景          |

如果 `final-fast.mp4` 不存在或过期，先 `cd .tmp/demo-video/remotion-final && npx remotion render` 重渲，渲不动就 ask 用户。

---

## 2. 模型选型 — 2026-05 当下最佳组合

> ⚠️ AI 模型迭代极快，下面信息是 2026-05 调研当时的事实。**首次调用前，先快速 ping 一下两个 API 的 model list 端点确认型号名仍可用**，若发现已升级到 3.2 Pro / Qwen4-VL 之类，**直接换用更新版**，不要原地等。

### 主审：Gemini 3.1 Pro（首选）

- 上下文：**1M tokens**，原生吃 **单段视频上限 1 小时**
- 我们 4 分钟视频 → 完全在能力内
- 接入：Google AI Studio (`https://aistudio.google.com`) 或 Gemini API (`generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro:generateContent`)
- 视频上传：用 [File API](https://ai.google.dev/gemini-api/docs/files)（`files.upload` → 拿 `file.uri` → 在 `generateContent` 里引用），不要 base64 inline（4 分钟 1080p mp4 太大）
- 计价：$2/M input, $12/M output（thinking_level=HIGH 可选，但审片任务 MEDIUM 即可）
- 环境变量：`GEMINI_API_KEY`

### 交叉验证：Qwen3-VL-235B-A22B-Instruct

- 256K interleaved 上下文，原生 text+image+video
- 优势：国内可直连无代理痛点；视频时间戳定位能力强（技术报告 arxiv 2511.21631 专门强调 temporal grounding）
- 接入二选一：
  - **DashScope SDK**（推荐，国内）：`dashscope` Python/Node 包，`model="qwen3-vl-max"` 或 `qwen3-vl-plus`
  - **OpenRouter**：`openrouter.ai/qwen/qwen3-vl-235b-a22b-instruct`，统一 OpenAI 兼容接口
- 环境变量：`DASHSCOPE_API_KEY` 或 `OPENROUTER_API_KEY`

### 备选（如果上面两个都跑不动）

- **GLM-4.6V**（智谱 BigModel，128K，国内）
- **Kimi-VL-A3B-Thinking**（Moonshot，国内）

**严禁**：GPT-4o 抽帧 / Claude 抽帧路线。这次要的是模型对**动效、转场、字幕动画、Screen Studio 感**的判断，抽帧全废。

---

## 3. 审片维度与权重

按重要度（高→低）排列，是给 prompt 模板用的：

| 维度                    | 权重 | 关注点                                                                         |
| ----------------------- | ---- | ------------------------------------------------------------------------------ |
| **subtitles**     | 25%  | 玻璃感是否通透、对比度、字号、易读、动效自然度（不要"机械跳出"）               |
| **screen_studio** | 20%  | zoom/pan 节奏、鼠标光标是否平滑、点击波纹是否过度、整体"录屏感"vs"做作感"      |
| **transitions**   | 15%  | 段间衔接是否电影感，white flash / crossfade / slide 是否过度或不足             |
| **pacing**        | 15%  | 哪段拖、哪段急、信息密度曲线                                                   |
| **brand**         | 10%  | Logo Reveal 震撼度、Outro 收尾、整体视觉品牌一致性                             |
| **audio_sync**    | 10%  | 旁白对齐字幕、关键 beat 是否落点（虽然 BGM 还没加，先记录"该有 beat"的时间点） |
| **overall**       | 5%   | 整体观感：专业 / 廉价 / 做作 / 大气 / 病感（医疗 App 不能太冷峻或太轻浮）      |

---

## 4. 提交给模型的 prompt 模板

中文 system prompt 模板，两个模型都用同一份（Qwen3-VL 也能吃中文）：

```
你是一名顶级产品演示视频导演兼后期审片师，曾给 Apple Keynote、Linear、Figma 的发布会做过审片。

输入：一段 4 分钟的医疗 App 产品演示视频（中文），结构为 Intro / AE 概念 / 学生端 / 教师端 / 双端实时 / Outro 六段。

任务：以"严苛但建设性"的视角审片，输出结构化 JSON 数组，每条问题必须可执行（即工程师/设计师拿到就能直接动手改）。

审片维度（按权重）：
- subtitles（25%）：玻璃感、对比度、字号、动效
- screen_studio（20%）：zoom/pan、鼠标、点击波纹
- transitions（15%）：段间衔接
- pacing（15%）：节奏
- brand（10%）：Logo / Outro / 视觉一致性
- audio_sync（10%）：旁白对齐
- overall（5%）：整体气质

特别关注（导演指定）：
1. 字幕"玻璃感"是否高级、通透，还是糊、白、机械
2. Screen Studio 感是否自然，鼠标光标动作是否像真人
3. 是否有"做作"、"廉价"、"廉价模板感"
4. 医疗 App 气质：稳重 + 现代 + 温暖，避免冷峻或轻浮

输出格式（严格 JSON，禁止任何额外文本）：
{
  "summary": "一段不超过 150 字的整体评价",
  "scores": {
    "subtitles": 0-10,
    "screen_studio": 0-10,
    "transitions": 0-10,
    "pacing": 0-10,
    "brand": 0-10,
    "audio_sync": 0-10,
    "overall": 0-10
  },
  "issues": [
    {
      "ts": "MM:SS",
      "ts_end": "MM:SS",  // 可选
      "section": "intro|ae|d1|d2|d3|outro",
      "category": "subtitles|screen_studio|transitions|pacing|brand|audio_sync|overall",
      "severity": "critical|major|minor",
      "observation": "你看到的现象（描述，不评判）",
      "issue": "为什么这是问题（评判）",
      "suggestion": "具体怎么改（动手级别，含组件/参数/路径）"
    }
  ],
  "top5_fixes": [
    {"rank": 1, "ts": "...", "fix": "...", "estimated_impact": "high|medium|low"}
  ],
  "highlights": [
    "做得好的地方，列 3-5 条，避免一边倒只批评"
  ]
}

要求：
- issues 至少 15 条，覆盖 6 个段落都要有
- ts 必须精确到秒（你看视频时记录的时间戳）
- suggestion 必须具体到组件/参数级，禁止"建议优化字幕"这种空话
- 中文输出
```

---

## 5. 工程落地

### 5.1 目录结构

```
.tmp/demo-video/
  judge/
    judge-gemini.mjs       # 主审脚本（Gemini 3.1 Pro）
    judge-qwen.mjs         # 交叉验证脚本（Qwen3-VL）
    merge-reports.mjs      # 合并两份报告，标注一致/分歧项
    report-gemini.json
    report-qwen.json
    report-merged.md       # 人类可读的最终报告
```

### 5.2 judge-gemini.mjs 骨架

- Node 20+，用 `@google/genai` 官方 SDK 或者直接 `fetch`
- 流程：
  1. `files.upload(mp4)` → 拿 `file.uri`
  2. 轮询 `files.get(name)` 直到 `state === "ACTIVE"`
  3. `generateContent({ model: "gemini-3.1-pro", contents: [{role: "user", parts: [{file_data: {file_uri, mime_type: "video/mp4"}}, {text: SYSTEM_PROMPT}]}], generationConfig: { responseMimeType: "application/json", thinkingConfig: { thinkingLevel: "MEDIUM" } } })`
  4. 解析 JSON → 写盘
- 错误兜底：429 退避 60s 重试 3 次；JSON 解析失败时把原 raw 也保存便于排查

### 5.3 judge-qwen.mjs 骨架

- 用 DashScope SDK（`dashscope` npm 包）或 fetch DashScope HTTP
- 同样上传视频文件 → 拿 video URL 或 OSS 引用
- model: `qwen3-vl-max-latest`
- 同一份 SYSTEM_PROMPT，要求 JSON 输出

### 5.4 merge-reports.mjs

- 读两个 JSON
- 按 `ts ± 3s` 容差对齐问题
- 输出 `report-merged.md`：
  ```markdown
  # 医小管演示视频 — AI 审片合并报告

  生成时间：YYYY-MM-DD HH:MM
  审片模型：Gemini 3.1 Pro + Qwen3-VL-Max

  ## 总分对比
  | 维度 | Gemini | Qwen | 均值 |
  ...

  ## 一致问题（两个模型都指出，高置信度）
  - [01:23] [subtitles/major] 字幕 ... 建议 ...

  ## 分歧问题（仅一个模型指出，需人工判定）
  - [Gemini-only / 02:15] ...
  - [Qwen-only / 03:40] ...

  ## Top 修复优先级（综合两份 top5_fixes）
  1. ...
  2. ...

  ## 做得好的地方
  - ...
  ```

---

## 6. 执行步骤

1. **环境准备**

   - 申请 / 复用 `GEMINI_API_KEY`（Google AI Studio 免费档可起步）和 `DASHSCOPE_API_KEY`（百炼控制台）
   - 写到 `.tmp/demo-video/.env`（gitignored）
   - 安装依赖：`pnpm i @google/genai dashscope dotenv`
2. **快速 API 健康检查**（5 分钟）

   - 上传一张 1KB 测试图给两个 API，确认 key 有效、模型名仍可用
   - **如果发现 Gemini 3.2 Pro / Qwen4-VL 已 GA，切到新版**
3. **跑 Gemini 主审**

   - 上传 final-fast.mp4
   - 发请求，等响应（视频长度 4min，模型推理 + thinking 估计 30-90s）
   - 解析 JSON，落盘
4. **跑 Qwen 交叉验证**

   - 同上
5. **跑 merge-reports.mjs**

   - 产出 `report-merged.md`
6. **人工 1 分钟扫一眼**

   - 看 top5 是否合理，是否有明显胡说（比如说"字幕用了 Helvetica"——我们用的是 Noto Sans SC）
   - 如果发现模型在某段明显出错，在 report 末尾加 `## 人工修订` 标注
7. **提交**

   - `git add .tmp/demo-video/judge/`
   - `git commit -m "feat(demo): T18 AI video judge — Gemini 3.1 Pro + Qwen3-VL"`
   - 把 `report-merged.md` 路径回报给导演

---

## 7. 验收门槛

- ✅ `report-gemini.json` 和 `report-qwen.json` 均存在且符合 schema
- ✅ `report-merged.md` 含至少 15 条 issues，覆盖 6 个段落
- ✅ 每条 issue 含 `ts` / `category` / `severity` / `suggestion`，suggestion 必须可操作
- ✅ Top5 修复清单按 estimated_impact 排序
- ✅ 至少 3 条 highlights（避免一边倒批评）
- ✅ 总执行时间 < 30 分钟（不含 API 排队等待）

---

## 8. 常见坑预警

1. **Gemini File API 上传超时**：4min 1080p mp4 可能 > 100MB，HTTP/1.1 上传不稳，必须用 SDK 的 resumable upload；或者先 `ffmpeg -c copy` 一次重封装（不重编码，秒级）压到 ≤ 50MB
2. **Qwen DashScope 视频引用**：DashScope 视频不接受任意本地路径，需要先上传到 OSS 拿公网 URL，或用 base64（< 20MB 限制）。如果 mp4 > 20MB，先 `ffmpeg -vf scale=1280:-2 -c:v libx264 -crf 30` 压一份 720p 副本专供 Qwen
3. **模型输出非纯 JSON**：哪怕设了 `responseMimeType: "application/json"`，偶尔会包 markdown ``json`` 代码块。用 `JSON.parse` 前先剥壳
4. **时间戳错位**：模型可能把"AE 段第 30 秒"算成"全片 30s"或"AE 段内 30s"。在 prompt 里明确"ts 是从视频 0:00 算起的绝对时间戳"
5. **模型幻觉**：模型可能编造不存在的细节（"3:25 处字幕拼写错误"，但其实没字幕）。merge 阶段如果只有一个模型指出 + 听起来很奇怪 → 标 `low_confidence` 让人工核
6. **不要陷入 API 比价细节**：审片任务总成本 < $1，别花半小时调参数省 $0.10

---

## 9. 超出范围（本任务不做）

以下属 T19 收尾五件套，不在 T18 内：

- BGM 选型
- SRT 字幕导出
- 响度归一化（EBU R128）
- 最终 H264 二压
- 封面图生成
- 真正的 polish 实施（T18 只产报告，不动 Remotion 源码）

---

## 10. 完成后回报格式

```
T18 完成 ✅
- Gemini 评分均值: X.X / 10
- Qwen 评分均值: X.X / 10
- 一致 critical 问题: N 条
- 一致 major 问题: N 条
- Top 3 推荐先修:
  1. [MM:SS] ...
  2. [MM:SS] ...
  3. [MM:SS] ...
- 报告: .tmp/demo-video/judge/report-merged.md
- API 总花费: $X.XX
```

— END —
