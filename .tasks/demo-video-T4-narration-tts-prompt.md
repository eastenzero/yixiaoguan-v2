# 副窗口任务 · T4 配音 TTS 生成

> 2026-05-12 凌晨 主对话导演产出
> 目标：给医小管产品演示长片生成 5 段中文配音 mp3
> 当前阶段：文案早已定稿，等你跑 TTS

---

## 仓库 / 工作目录

```
F:\Documents\code\yixiaoguan-v2
```

---

## 一句话目标

根据 `@F:\Documents\code\yixiaoguan-v2\video\07-narration-script.md` 表格里的"旁白"列文案，生成 5 段 mp3，放到 `.tmp/demo-video/voice/`，给后续 Remotion 编排（T14）填进时间轴。

---

## 必读

**唯一文案来源**：`@F:\Documents\code\yixiaoguan-v2\video\07-narration-script.md`

那份文档里：
- **Intro 段（0-8s）** 是**纯静音 BGM**，不需要配音 — 跳过
- **AE / D1 / D2 / D3 / Outro** 共 5 段，每段表格里有"旁白"列就是要念的中文文本
- 文档"总体设定"和"备选语气方向"章节说明风格 = **沉稳产品发布会 + 校园亲切感**，**女声优先**

---

## 输出（最终交付）

```
.tmp/demo-video/voice/ae.mp3      99 字, 目标 30s
.tmp/demo-video/voice/d1.mp3     177 字, 目标 70s
.tmp/demo-video/voice/d2.mp3     200 字, 目标 70s
.tmp/demo-video/voice/d3.mp3     149 字, 目标 50s
.tmp/demo-video/voice/outro.mp3   19 字, 目标 10s（最后 3s 应为静音 padding 给 BGM 渐出）
```

**音频参数统一**：
- MP3 192 kbps
- 单声道
- 22.05 kHz 或 44.1 kHz（统一即可）
- 头尾不要 dead air（如有，用 ffmpeg 自己 trim）

**时长偏差容忍**：±20%（如 D1 目标 70s，实际 56-84s 都接受 — Remotion 阶段会做 video timing 微调）

---

## 配音参数

| 项 | 值 |
|---|---|
| 语言 | 中文普通话 |
| 性别 | **女声**优先（更亲和，校园语境贴合）；如果 API 没好女声再用男声 |
| 风格 | 沉稳、聚焦、产品发布会 + 一丝校园亲切感（不油不刻意） |
| 语速 | 中速 ~4 字/秒（参考 07 文档"字密度"列校准） |
| 情感 | "信任感"为主，AE 段稍冷静，D2 知识库段稍温暖，D3 高潮段不要 over-act |

如果 TTS API 支持 SSML / 情感标签，可以加 `<break time="500ms"/>` 切句子、用 `style="newscast"` / `serious-news` / `gentle` 等中文情感预设增强质感。

---

## 推荐 API 选型

按这个顺序探测，**一个能用就直接干**（不必非要 A/B 全跑完）：

| 优先级 | API | 推荐音色 | API Key 环境变量 |
|---|---|---|---|
| ⭐⭐⭐ | **阿里云 DashScope CosyVoice v2** | `longxiaochun_v2`（女）/ `longyumi_v2`（女，更温暖） | `DASHSCOPE_API_KEY` |
| ⭐⭐⭐ | **火山引擎语音合成 v3** | `BV701_streaming`（女，知性）/ `zh_female_qingxin` | `VOLC_AK` + `VOLC_SK` 或 `VOLC_APP_ID` + `VOLC_ACCESS_TOKEN` |
| ⭐⭐ | **Azure Neural Speech** | `zh-CN-XiaoxiaoNeural`（女，最强）/ `zh-CN-YunxiNeural`（男） | `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` |
| ⭐ | **ElevenLabs** | 中文一般，最后选项 | `ELEVENLABS_API_KEY` |

**首选 CosyVoice v2 longxiaochun_v2** —— 国内 TTS 最自然，校园场景适配最好，DashScope 注册即送大量免费额度。

### 怎么找 API Key

按这个顺序找：
1. 仓库根 `.env` 文件
2. `services/gateway/.env`
3. 系统环境变量（PowerShell: `$env:DASHSCOPE_API_KEY`）
4. `deploy/.env.example` 看看变量名格式
5. 用户内存里可能记录的（如果你有访问权限）

**全部都没找到** → 回报主对话："xxx API key 缺失，请提供"。不要硬编码任何 key 到脚本。

---

## A/B 测试（可选，时间紧可跳）

如果同时有 2+ 家 API 的 key，先做 A/B：

1. 仅跑 **D2 数据看板段**（200 字 / 20s 那段，文案见 07 文档 D2 表格第二行）
2. 每家 API 出一版 `.tmp/demo-video/voice/_ab/d2_sample_{provider}.mp3`
3. 把所有 A/B 样本路径回报主对话，**等用户盲听投票后**再跑剩下 4 段

如果只有 1 家 API → 跳过 A/B，直接跑全部 5 段。

---

## 工程化建议

写一个**可复用的脚本**而不是手动一段一段跑：

```
.tmp/demo-video/gen-narration.mjs   或   gen-narration.py
```

脚本职责：
1. 读 `video/07-narration-script.md` 解析表格，拿 5 段（AE/D1/D2/D3/Outro）的"旁白"列
2. 自动剥离 Markdown 装饰（如「」引号可保留，但不要让"|"管道符进 TTS）
3. 调 TTS API（CosyVoice / VolcEngine / Azure 任一）按段生成 mp3
4. 输出到约定路径
5. 终端打印每段实际时长 + 字数 + 字密度对比，方便检查

**为什么要脚本而不是手动**：用户后续可能想换音色 / 换 API / 调整文案重跑，脚本化让重跑成本 = 1 行命令。

---

## 不要做的事

- ❌ 不要 commit 任何 mp3 文件（体积偏大，留本地即可。如果需要 commit 一份用于 demo 演示的最终版，主对话会单独决定）
- ❌ 不要修改 `video/07-narration-script.md` 文案
- ❌ 不要给配音加 BGM 或音效（BGM 是 T14 Remotion 阶段统一加）
- ❌ 不要自己加 intro 段配音（intro 是 BGM 静音段）
- ❌ 不要做任何降噪 / EQ / 压缩处理（TTS 输出已经够干净，Remotion 阶段统一处理）
- ❌ 不要换文案 / 改标点 / 重写语气（07 文档是契约，逐字照念）

---

## 验收清单

主对话验收时会看：

- [ ] 5 个 mp3 文件齐全在 `.tmp/demo-video/voice/`
- [ ] 每段时长在 ±20% 目标值范围内
- [ ] 总时长 5 段合计 230s ± 20%
- [ ] 中文发音清晰、不结巴、不漏字、不串读
- [ ] 风格统一（女声 + 沉稳 + 不油腻）
- [ ] 数字 / 英文（如 "16 项" / "AI" / "847" / "73%"）发音正常（必要时在文案前预处理成中文数字）
- [ ] 头尾无 dead air（开头不要等 0.5s 才出声）
- [ ] 用过的 TTS API / 音色名记在 `.tmp/demo-video/voice/README.md` 里，主对话好复盘

跑完了告诉主对话：
1. 用了哪家 API + 哪个音色
2. 5 段 mp3 路径 + 实际时长
3. gen-narration 脚本路径（方便重跑）
4. 你认为哪段质量最好 / 最差（用户的二次决策参考）

---

## 卡壳怎么办

- API 全没 key → 立刻回报，不要瞎试免费 demo 接口（质量没保证）
- 某段时长严重偏长（>120% 目标）→ 加 SSML break 或调 speech_rate 1.1-1.2，再不行回报主对话商量是不是要砍文案
- 中文里夹的英文字母（"AI"）读成"A-I"分开念 → 用 SSML `<sub alias="爱艾">AI</sub>` 之类替换
- 火山引擎 / Azure 的鉴权 SDK 装不上 → 优先换 CosyVoice（DashScope SDK 最简单，`dashscope` pip 一行）

回报时附上：错误日志 + 试过的 API + 当前进度。
