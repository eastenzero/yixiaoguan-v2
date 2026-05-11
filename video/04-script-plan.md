# 04 · 剧本契约（导演定稿 v3）

> 2026-05-11 晚导演会议产出 · 所有 AI 子代理与人工执行者从本文件接齐。
> 上游：`@F:\Documents\code\yixiaoguan-v2\video\01-tech-feasibility.md` · `@F:\Documents\code\yixiaoguan-v2\video\02-pages-inventory.md` · `@F:\Documents\code\yixiaoguan-v2\video\03-ae-template-analysis.md`

---

## 0. 决策记录（Immutable）

| 项 | 值 | 来源 |
|---|---|---|
| 形态 | 产品演示长片（功能展示 > 宣传片） | 用户 2026-05-11 |
| 总时长 | 4-5 分钟 | 同上 |
| 主角视角 | 双视角并行（学生端 + 教师端 + 双端实时高潮） | 同上 |
| 高潮镜头 | D3 双端**左右并排分屏**实时对话 45-60s | 同上 |
| 录制环境 | 内网 165 dev（实时推送已 e2e 验证） | 同上 |
| UI 优化策略 | 用户单独开会话推进，本对话不涉入 | 用户 2026-05-11 |
| 输出格式 | **1920×1080 横屏 30fps H.264**（推断：用户提到"左右两边加动效字效"，竖屏空间不足） | Cascade 推断 |
| 字体 | 思源黑体 CN（Noto Sans SC）+ Lato（AE 模板自带） | 01 文档 |
| 品牌主色 | `#7C3AED` 紫 | 01 文档 |
| AE 模板 | App Promo Phone 14 Pro Mockup Pack（Videohive 40526693） | 03 文档 |

---

## 1. 整片时间轴（v1 骨架，单位秒）

```
00:00 ─┬─ Intro                       (8s,  stock 开场)
00:08 ─┼─ AE 概念片头                  (30s, 5-6 个无 logo SCENE)
00:38 ─┼─ D1 学生端核心闭环             (70s)
01:48 ─┼─ D2 教师端能力                (70s)
02:58 ─┼─ D3 双端实时分屏 ⭐           (50s, 左右并排)
03:48 ─┼─ Outro                       (10s, logo + slogan)
03:58 ─┴─ END
```

弹性区间：D1/D2 各 ±15s，D3 ±10s。如果需要压缩到 4 分钟整，从 D1/D2 各砍 10s。

---

## 2. 每段录制约定

### 2.1 Intro 8s（用户负责素材）

- 形式：stock 视频 + logo
- 候选风格：科技感粒子展开 / 校园航拍 / 学生使用手机的剪影
- 配音：**无台词**，仅 BGM 渐入
- 字效：logo + slogan 末尾入场 fade-in

### 2.2 AE 概念片头 30s（5-6 SCENE）

按 03 文档场景表，初选如下（**待 UI 完成后定稿截图再调**）：

| 顺序 | SCENE | 时长 | 屏幕内容 | 文字（AE Text Holder） |
|---|---|---|---|---|
| 1 | SCENE_01 (8s 单屏特写) | 8s | 学生端 home 首屏 | 「智能问答 · 秒答常见问题」 |
| 2 | SCENE_05 (8s 单屏特写) | 8s | 学生端 chat 流式答 | 「AI 流式回答」 |
| 3 | SCENE_10 (10s 双屏对比) | 10s | 学生 chat × 教师 dashboard | 「学生有问 · 老师在场」 |
| 4 | SCENE_13 (8s 双屏) | 8s | 学生 services × 教师 analytics | 「全场景洞察」 |

合计 34s（裁掉一两秒过场即可对齐 30s 概念）。

> 备选 SCENE_04 / 06 / 08 / 09 / 15 详见 03 文档。

### 2.3 D1 学生端核心闭环 70s

- **视口**：iPhone 14 Pro emulation 393×852 + DPR 3
- **URL**：内网 165 dev `http://192.168.100.165:3001/#/`（待 UI 完成确认）
- **登录账号**：4124150001 / 4124150001（参考 prod 凭证）

**镜头序列**：

| 起-止 | 时长 | 操作 | 字效（左右） | 配音 |
|---|---|---|---|---|
| 38-46 | 8s | 登录页输入学号 → 进入 home | "新用户登录" 数字滚动 | 介绍学生端定位 |
| 46-54 | 8s | home 快速浏览（问候/快捷/服务卡） | "16 项校园服务" 数字 | 列举功能 |
| 54-1:10 | 16s | 点 AI 问答 → 提问"宿舍电费怎么交" → AI 流答（**镜头跟随高度采样**） | "AI 流式输出" 闪烁 + 字数计数 | 强调 AI 速答 |
| 1:10-1:20 | 10s | 打开来源弹层 → 翻历史 | "知识溯源" 角标 | 提到知识库支撑 |
| 1:20-1:32 | 12s | 提复杂问题 → 触发"转人工" | "转人工 · 老师在线" 弹出 | 引出 D3 |
| 1:32-1:48 | 16s | 等待 + buffer | — | 总结过渡 |

### 2.4 D2 教师端能力 70s

- **视口**：1920×1080 desktop（教师端虽是 H5 mobile-first，但桌面浏览器更适合数据看板展示）
- **URL**：内网 165 dev 教师端
- **登录账号**：anjing / Anjing@yxg2026

**镜头序列**：

| 起-止 | 时长 | 操作 | 字效 | 配音 |
|---|---|---|---|---|
| 1:48-1:58 | 10s | 登录 → 工作台 hero 卡 + 4 数据卡 | "工作台总览" | 老师视角切入 |
| 1:58-2:18 | 20s | 进入数据看板（4 卡 + 趋势 + 学院分布 + 时段热力 + AI 成本） | "847 提问 / 73.2% 解答率" 滚动 | 强调数据驱动 |
| 2:18-2:38 | 20s | 知识库 → 高频待补卡片 → 点"去补充" → 编辑入库 | "知识沉淀闭环" | AI 答不了的，老师补 |
| 2:38-2:58 | 20s | profile 紫粉 hero + 切入 D3 触发上下文 | "实时受理就绪" | 引出双端通信 |

### 2.5 D3 双端实时分屏 ⭐ 50s

**这是全片最技术、最炫的一段**。

**录制方案**（详见 §4 D3 技术细节）：
- Playwright 双 page 并行录制：student 393×852 + teacher 393×852
- 同步 t0 = `Date.now()` 锚点写入两端 events.json
- 输出 `student.mp4` + `teacher.mp4` 两个独立视频

**Remotion 编排**：
```tsx
<AbsoluteFill style={{ background: '#0F0A1F' }}>
  <div style={{ display: 'flex', height: '100%' }}>
    <div style={{ flex: 1, position: 'relative' }}>
      <OffthreadVideo src={staticFile('student.mp4')} />
      <Label>学生端</Label>
    </div>
    <MessageBeam />  {/* 中间发光横线，消息事件触发脉冲 */}
    <div style={{ flex: 1, position: 'relative' }}>
      <OffthreadVideo src={staticFile('teacher.mp4')} />
      <Label>教师端</Label>
    </div>
  </div>
</AbsoluteFill>
```

**镜头序列**：

| 起-止 | 时长 | 学生端 | 教师端 | 中间字效 |
|---|---|---|---|---|
| 2:58-3:08 | 10s | 复杂问题已转人工，"等待中" | 工作台 → 收到红点提醒 | "实时推送 · WebSocket" |
| 3:08-3:20 | 12s | 等待动画 | 点开 detail，看到学生消息 | "Centrifugo 频道：conv:N + user#N" |
| 3:20-3:35 | 15s | 收到第一条老师消息 → 后续连发 | 老师打字 → 一句话连发多条 | 中间发光横线脉冲（每发一条） |
| 3:35-3:48 | 13s | 学生回复"谢谢"，对话顺畅 | 老师标记"已解决" | "对话 · 流畅 · 端到端" |

### 2.6 Outro 10s

- logo + slogan + 联系方式
- 配音：项目 slogan 一句
- BGM 渐出

---

## 3. 输出格式约定（Immutable）

| 项 | 值 |
|---|---|
| Composition | 1920×1080 |
| 帧率 | 30fps |
| 编码 | H.264 |
| 容器 | mp4 |
| 音频 | AAC 320kbps stereo |
| 子轨 | 配音轨 + BGM 轨（FFmpeg 混音 -filter_complex amix） |
| 字幕 | Remotion 内置组件硬字幕（精确对齐配音文案） |

**视频元素布局（横屏舞台）**：

```
┌──────────────────────────────────────────────┐
│           ↑ 1080                             │
│  ┌──────┐                          ┌──────┐  │
│  │ 字效 │     ┌──────────────┐     │ 字效 │  │
│  │ 左侧 │     │              │     │ 右侧 │  │
│  │      │     │  录制内容       │     │      │  │
│  │ 数字 │     │  (mobile or   │     │ 数字 │  │
│  │ 文字 │     │   desktop)    │     │ 文字 │  │
│  │ pulse│     │              │     │ pulse│  │
│  │      │     └──────────────┘     │      │  │
│  └──────┘   ←──── 1920 ────→     └──────┘  │
│         字幕带（底部胶囊）                  │
└──────────────────────────────────────────────┘
```

- D1/D2 mobile 录制：中央放 405×880（393×852 等比放大 1.03×），左右各 757px 字效空间
- D2 desktop 录制：直接铺满 1920×1080
- D3 分屏：左右各 540×1170（393×852 等比放大 1.37×），中间留 840px 字效空间，上下各裁掉 45px

---

## 4. D3 双 page Playwright 录制技术细节

### 4.1 文件骨架（待 UI 完成后由 Kimi 改造完成）

```js
// .tmp/demo-video/record-d3.mjs
import { chromium } from 'playwright';

const STUDENT_URL = 'http://192.168.100.165:3001/#/';
const TEACHER_URL = 'http://192.168.100.165:3000/#/';  // 待确认端口
const OUT = 'out/d3';

const browser = await chromium.launch({ headless: false });

// 同步 t0
const t0 = Date.now();
await fs.writeFile(`${OUT}/sync.json`, JSON.stringify({ t0 }));

const studentCtx = await browser.newContext({
  viewport: { width: 393, height: 852 },
  deviceScaleFactor: 3,
  isMobile: true,
  hasTouch: true,
  userAgent: 'Mozilla/5.0 (iPhone; ...)',
  recordVideo: { dir: `${OUT}/student`, size: { width: 393, height: 852 } },
});
const teacherCtx = await browser.newContext({
  viewport: { width: 393, height: 852 },
  deviceScaleFactor: 3,
  isMobile: true,
  hasTouch: true,
  recordVideo: { dir: `${OUT}/teacher`, size: { width: 393, height: 852 } },
});

const studentPage = await studentCtx.newPage();
const teacherPage = await teacherCtx.newPage();

// events 同时写入 t0 锚点
const studentEvents = [];
const teacherEvents = [];
const log = (arr, label, extra = {}) => {
  arr.push({ t: Date.now() - t0, label, ...extra });
};

// 1. 学生端登录已经升级了的工单
await studentPage.goto(STUDENT_URL);
log(studentEvents, 'load');
// ... 登录逻辑 ...

// 2. 教师端登录到 detail.vue 状态
await teacherPage.goto(TEACHER_URL);
// ... 教师登录 + 进入 detail 等待新 escalation ...

// 3. 学生触发转人工（前置准备）
// 这部分预先在 D1 段已完成，现在打开新会话直接转人工

// 4. 老师收到 → 接单 → 打字 → 发送
// 5. 学生端实时收到 → 学生回应

// 录制完关闭前导出 events
await fs.writeFile(`${OUT}/student/events.json`, JSON.stringify(studentEvents));
await fs.writeFile(`${OUT}/teacher/events.json`, JSON.stringify(teacherEvents));
await browser.close();
```

### 4.2 Remotion 时间轴对齐

- 两端视频起始 frame = `Date.now() (录制开始)` - `t0`
- 用 `<Sequence from={offsetFrames}>` 错位嵌入两端视频
- 中间 MessageBeam 脉冲触发时间 = `events.json` 里"消息发送"事件的 `t`

### 4.3 关键风险

| 风险 | 缓解 |
|---|---|
| 双 page 录制 CPU 飙高，丢帧 | 30fps，单 page 资源占用约 8% CPU on M1，双 page 可承受 |
| 两端视频时长不一致（一端先关） | 关停时机统一靠 `Promise.all` |
| 教师端推送链路偶发延迟 | D3 录制前先做一次 dry-run 确认推送 |

---

## 5. 派单分工矩阵

| 任务 ID | 内容 | 派给 | 工时 | 阻塞条件 |
|---|---|---|---|---|
| **T0** | commit `video/` 目录 | Kimi（主仓 git） | 5min | 无 |
| **T1** | 04 剧本契约（本文件） | Cascade | ✅ 完成 | — |
| **T2** | A2 配音文案大纲（4-5 分钟分段） | Cascade | 60min | T1 |
| **T3** | A4 AE 段每屏短文字定稿 | Cascade | 30min | T1 |
| **T4** | A5 配音 API A/B（4 家各 30s 样本） | Cascade + 用户试听 | 90min | T2 |
| **T5** | C1 AE .jsx 批量替换脚本骨架 | Cascade | 90min | T3 |
| **T6** | D3 双 page Playwright 框架代码 | Cascade | 60min | T1 |
| **T7** | UI 优化（学生 + 教师演示路径） | **用户单独会话** | 1.5-2 天 | — |
| **T8** | B1+B2 截图（基于 T7 polished UI） | Kimi | 4h | T7 ✅ |
| **T9** | 测试数据填充（anjing 工单 + 学生提问） | Codex 或 Cascade | 2h | T7 ✅ |
| **T10** | C3 AE 渲染 ae-segment.mp4 | Cascade（MCP）+ 用户验证 | 4h | T8 + T5 |
| **T11** | D1 学生端 demo 录制 | Kimi | 4h | T7 ✅ + T9 |
| **T12** | D2 教师端 demo 录制 | Kimi | 4h | T7 ✅ + T9 |
| **T13** | D3 双端 demo 录制 | Cascade + Kimi | 6h | T11 + T12 |
| **T14** | E Remotion 总编排（intro + AE + D1 + D2 + D3 + outro + 字幕 + 配音 + BGM） | opencode | 1.5 天 | T4 + T10 + T11 + T12 + T13 |
| **T15** | 总片渲染 + QA | Cascade + 用户 | 4h | T14 |

**关键路径**（最长）：T7 → T8/T9 → T11/T12 → T13 → T14 → T15 ≈ 5-6 天

---

## 6. 启动信号（UI 完成后回来读这个）

当用户在新对话里完成 Phase 0 UI 优化，回到本对话报信号 `UI 完成` 后，Cascade 立刻按下面 6 步推进：

1. 拉最新 master / `ui/student-polish-merge` 分支到主仓 + 165 dev
2. 165 dev 重启 student :3001 + teacher 服务，验证 UI
3. 起 T8 截图（Kimi）+ T9 测试数据（Codex）并行
4. T8 完成后立刻起 T10 AE 渲染（Cascade + MCP）
5. T8/T9 完成后并行起 T11/T12（Kimi 双进程）
6. T11/T12 完成后起 T13 D3，全部 demo 收口后交 T14 给 opencode 编排

**预期收口时间**：UI 完成后 4-5 天可出 v1 final.mp4。

---

## 7. 资源清单 TODO（待补）

- [ ] BGM：1 首主题曲（无版权，候选 Epidemic Sound / Artlist / YouTube Audio Library）
- [ ] 配音 API key（A5 试听后定）
- [ ] 字体：Noto Sans SC ttf（Google Fonts 免费）
- [ ] 项目 logo：高分辨率 PNG / SVG（用户提供）
- [ ] Outro slogan 文案（用户敲定，建议 8 字以内）
- [ ] Intro stock 素材（用户从 Pexels / Pixabay / Storyblocks 找）

---

## 8. 验收标准

- [ ] 总时长 4-5 分钟
- [ ] 1920×1080 30fps H.264 mp4
- [ ] 配音 + BGM 已混音，无破音
- [ ] 字幕硬挂在视频上，与配音对齐误差 < 200ms
- [ ] AE 段所有 SCENE 屏幕内容已替换为医小管真实截图
- [ ] D3 双端时间轴对齐误差 < 200ms（教师发出动作 → 学生收到，肉眼无察觉延迟）
- [ ] 所有镜头 UI 一致（同 polished UI 版本，无 D 段半路换 UI 风格）

---

## 9. 历史

- **v3 · 2026-05-11 晚** — 导演会议产出，确定形态/时长/视角/分屏/录制环境/输出格式
- v2（已废弃）— 90s 短宣传片
- v1（已废弃）— 60s 极短片
