# 医小管 宣传视频 · 技术可行性分析

> 第一稿 · 2026-05-11
> 状态：**PoC v1 已跑通**，主路径技术可行性已验证

---

## 摘要 (TL;DR)

用 **Playwright 录屏 + Remotion 后处理** 这条全代码可控的流水线，可以做出商业级的医小管产品演示视频，且全程 **AI 驱动**（脚本/配音/字幕/编排都用代码或 API），用户的手动工作只剩 **Rotato/AE 开场片段** 一项。

PoC 已验证：22 秒 student-app 演示 → 渲染 1080×1920 竖屏 mp4，带 zoom 镜头跟随 + 光效脉冲点 + 文字标注。

后续工程化的所有环节（AI 流式镜头跟随、teacher-app 三场景、双端实时对话、中文配音、字幕、配乐）**没有不可解决的技术风险**，但有几处需要在脚本规划阶段就考虑清楚。

---

## 一、整体技术架构

```
┌──────────────────────────────────────────────────────────────┐
│                       脚本规划（人工）                          │
│       场景表 = [时间 | 镜头 | 旁白 | 字幕]，三层时间对齐         │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
   ┌─────────────────────┴────────────────────┐
   │                                          │
┌──┴──────────────┐                ┌──────────┴────────┐
│ Playwright 录屏 │                │ Rotato/AE 开场片段 │
│  - mobile/desk  │                │  - 设备 3D 翻转    │
│  - emit events  │                │  - 用户手动制作    │
│    JSON         │                │    导出 mp4       │
└──┬──────────────┘                └──────────┬────────┘
   │ demo.webm + events.json                  │ intro.mp4
   ↓                                          ↓
┌──┴──────────────────────────────────────────┴────────┐
│                Remotion 编排（React + Spring）        │
│  - 嵌入视频 OffthreadVideo                            │
│  - 根据 events 加 spring zoom + 光效脉冲 + 标注       │
│  - <Sequence> 拼接 intro / demo / outro              │
│  - 叠加字幕 + 配音 + 配乐                              │
└──────────────────────────┬────────────────────────────┘
                           ↓
                ┌──────────┴──────────┐
                │   ElevenLabs API    │  (AI 配音)
                │   FFmpeg 混音       │  (BGM)
                │   Whisper (可选)    │  (字幕兜底)
                └──────────┬──────────┘
                           ↓
                    final.mp4 (1080×1920)
```

### 各层工具表

| 层 | 工具 | 状态 | 备注 |
|---|---|---|---|
| 录屏 | Playwright (Node.js) | ✅ 已验证 | 系统装了 1.59.1，支持 mobile emulation + 视频录制 |
| 事件 timeline | 自写 mjs 脚本 | ✅ 已验证 | 输出 events.json，含 click 时间戳 + 坐标 + label |
| 后处理编排 | Remotion 4.x | ✅ 已验证 | React + spring + interpolate，渲染 30fps mp4 |
| 鼠标光标替代 | Remotion 光效脉冲 | ✅ 已验证 | 不录鼠标，纯 CSS 脉冲 ring 在 click 坐标显示 |
| 视频转码 | FFmpeg 8.0.1 | ✅ 已装 | webm → mp4，trim，混音 |
| 3D 设备开场 | Rotato / AE | ⚙️ 用户负责 | 用户手动出 5-10s 翻转片段 |
| AI 配音 | ElevenLabs / Azure TTS / 阿里云 TTS | 📋 待选型 | 中文质量需 A/B 测试 |
| 字幕 | Remotion 内置组件 / Whisper | 📋 待定 | 优先脚本字幕（精确），Whisper 兜底 |
| 配乐 | FFmpeg 混音（无版权 BGM） | 📋 待定 | Epidemic Sound / YouTube Audio Library |

---

## 二、PoC 验证记录

### 输入
- 目标 URL：`https://yxg.xiaoguan.site/#/`
- 视口：iPhone 14 Pro 393×852（学生端是 UniApp mobile 应用）

### 工程文件
| 文件 | 作用 | 引用 |
|---|---|---|
| 探查脚本 | 列出 DOM 可点击元素 | `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/probe.mjs` |
| 录制脚本 | Playwright 录屏 + 输出 timeline | `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/record-demo.mjs` |
| 时间戳记录 | 18 个事件，21.4s | `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/out/events.json` |
| Remotion composition | zoom + pulse + label 编排 | `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/remotion/src/Composition.tsx` |
| Remotion 入口 | 注册 Composition | `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/remotion/src/Root.tsx` |

### 输出
| 文件 | 内容 | 大小 |
|---|---|---|
| `out/demo.webm` | Playwright 原始录制 (含浏览器加载) | 1.58 MB · 46s |
| `out/demo-trimmed.mp4` | trim 后纯演示部分 (392×852) | 645 KB · 21s |
| `out/events.json` | 事件 timeline | 2.7 KB |
| `remotion/out/final-v1.mp4` | 最终渲染 (1080×1920) | 6.8 MB · 22s |

### 验证通过的能力
- ✅ Playwright 可录 mobile viewport (iPhone 14 Pro emulation)
- ✅ Playwright 可同步输出每个 click 的精确 ms 时间戳 + 坐标
- ✅ Remotion `OffthreadVideo` 可嵌入录制的 mp4
- ✅ Remotion `spring` + `interpolate` 可做丝滑 zoom + ease-in-out 节奏
- ✅ Remotion 可根据 events.json 自动定位 zoom 中心 + 显示标注
- ✅ Remotion 1080×1920 渲染速度：约 30 帧/秒（22s 视频用 30s 渲完）
- ✅ FFmpeg 可 trim webm + 转 mp4（无质量损失）

### 关键代码：zoom 算法
zoom 节奏实现见 `@f:/Documents/code/yixiaoguan-v2/.tmp/demo-video/remotion/src/Composition.tsx:48-77`，核心思路：
- 每个 click 触发 4 阶段：`lead-in (180ms) → peak (320ms) → hold (500ms) → ease-out (600ms)`
- 用 cubic ease-in-out 而非线性 → 视觉更顺
- zoom 时同步平移 video，让 click 点固定在 composition 中心

---

## 三、已决定的设计（无需再讨论）

### 3.1 用光效脉冲点替代鼠标光标
- **决策**：竖屏 mobile 演示场景下，光效比鼠标更原生、更酷
- **实现**：Remotion `<div>` + `transform: scale + opacity` 在 click 坐标做 0.5s 扩散动画
- **不做**：不再考虑 fake cursor 注入或 SVG 鼠标叠加

### 3.2 AI 流式输出 → 镜头跟随
- **决策**：录制时不打断 AI 流式输出，让镜头跟着答案逐字展开走
- **实现细节**（见第四章 4.1）：
  - Playwright 录制时用 `MutationObserver` 监听答案 div 高度变化，把 height 采样点写进 events
  - Remotion 后处理时根据 height samples 动态计算 video translateY，让答案底部始终在 viewport 中下部
  - 后期对"中段长时间打字"那段用 `<OffthreadVideo playbackRate={2}>` 加速 2-3×

### 3.3 Rotato / AE 开场用户自做
- **决策**：用户手动用 Rotato 或 AE 出 5-10s 设备 3D 翻转开场片段，导出 mp4
- **集成**：Remotion 用 `<Sequence>` 把 intro.mp4 / demo / outro.mp4 拼起来
- **接口约定**：用户产出的 mp4 须满足 1080×1920 竖屏 / H.264 / 30fps 否则 ffmpeg 预处理转码

### 3.4 Teacher App 三个核心场景
- **数据大屏**：desktop 1920×1080 viewport，注重数字滚动 + 图表动画
- **添加知识条目入库**：表单填写流程慢动作展示
- **跟学生端流式实时对话**：双端同时录制（最难，方案见 4.3）

### 3.5 总时长弹性 < 10 分钟
- 不强制时长，按内容质量决定
- 可能形态：60s 学生端 + 90s 老师端 + 30s 双端对话 ≈ 3 分钟全产品片
- 或：拆成多个短视频（30s 学生 / 30s 老师 / 45s 实时对话）独立投放

---

## 四、待解决的技术挑战与对策

### 4.1 AI 流式响应时间是黑盒（已有方案）

**问题**：点击 AI 问题后，流式回答耗时 3-30s 不可控，导致 timeline 漂移。

**方案**：录制时记录三个时间锚点 + 答案高度采样

```js
// 伪代码：record-demo.mjs 改造
await page.click('text=宿舍电费怎么交');
const t_clicked = now();

// 等到第一个字符出现
await page.waitForFunction(
  () => document.querySelector('.ai-answer')?.innerText?.length > 0,
  { timeout: 30000 }
);
const t_first_chunk = now();

// 持续采样答案高度，直到 2s 没新增
const heights = [];
let lastChange = now();
while (now() - lastChange < 2000) {
  const h = await page.locator('.ai-answer').evaluate(el => el.scrollHeight);
  heights.push({ time_ms: now(), height: h });
  if (heights.length >= 2 && h > heights[heights.length - 2].height) {
    lastChange = now();
  }
  await sleep(100);
}
const t_complete = now();

events.push({
  type: 'ai_streaming',
  t_clicked, t_first_chunk, t_complete,
  height_samples: heights,
});
```

Remotion 后处理时根据 `height_samples` 用 `interpolate` 平滑跟随。

**后期裁切冗余**：用 Remotion `<OffthreadVideo playbackRate={2.5}>` 把流式中段加速。

### 4.2 Teacher App 桌面端录制

**问题**：teacher-app 是 Vue3 + Element Plus 桌面应用，viewport 1920×1080，不能用 mobile emulation。

**方案**：Playwright 同套代码改 viewport
```js
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 2, // 让录制画质更清晰
  recordVideo: { dir: OUT_DIR, size: { width: 1920, height: 1080 } },
});
```
渲染时 composition 改成 1920×1080 横屏 composition，或者 1080×1920 竖屏内嵌横屏视频（带上下黑边或缩放展示）。

### 4.3 学生端 + 老师端实时对话同时录制（最难）

**问题**：要展示 teacher 端发消息 → student 端 AI 实时回复，需要双端同时录制并同步。

**方案候选**：

**A. Playwright 双 page 并行录制**（推荐）
```js
const studentPage = await context.newPage();
const teacherPage = await teacherContext.newPage();

await Promise.all([
  studentPage.goto('https://yxg.xiaoguan.site/#/'),
  teacherPage.goto('https://yxg-teacher.xiaoguan.site/'),
]);

// teacher 触发
await teacherPage.click('text=向学生发起问答');
// student 端 AI 自动响应
await studentPage.waitForSelector('.ai-answer');
```
两个 page 各自 `recordVideo`，输出 student.webm + teacher.webm。

Remotion composition 用左右分屏 (1080×960 上下 或 1920×1080 横屏左右)：
```tsx
<AbsoluteFill>
  <div style={{ flex: 1 }}>
    <OffthreadVideo src={staticFile('teacher.mp4')} />
  </div>
  <div style={{ flex: 1 }}>
    <OffthreadVideo src={staticFile('student.mp4')} />
  </div>
</AbsoluteFill>
```

**B. 屏幕实拍 + iPad/手机镜像**：把 teacher 投影到 desktop, student 投影到 iPad，用 OBS 同时录两个画面。**不推荐**，违背"全代码 AI 驱动"原则。

**关键技术点**：两个 Playwright page 录制的视频需要时间戳对齐。在录制开始前同步打一个时间戳 `t0_sync = Date.now()`，两个 events.json 都用这个 t0 算 offset，Remotion 根据 offset 对齐。

### 4.4 中文 AI 配音 API 选型（待 A/B 测试）

| 候选 | 优势 | 劣势 |
|---|---|---|
| ElevenLabs | 业内最好，情感丰富 | 中文质量稍弱于英文，按字符付费 |
| Azure Speech (Neural) | 中文质量很好，自然度高 | 需 Azure 账号，有起步免费额度 |
| 阿里云 智能语音交互 | 中文最优，本土化 | 国内服务，地理友好但 API 略繁琐 |
| 火山引擎语音合成 | 抖音级别中文质感 | 适合产品宣传调性 |

**建议**：3 家各做一段 30s 测试 → 用户盲听挑最合适的 → 锁定。

### 4.5 字幕策略

- **首选**：脚本里写好的旁白文字直接作为字幕（精确，无需转写）
- **方案**：Remotion 内置组件 + 时间戳手动对齐到旁白
- **兜底**：Whisper 本地转写（FFmpeg 已编译 whisper 支持），作为校对工具

### 4.6 视口与输出格式

- **学生端 demo**：录 393×852 竖屏 → 渲染 1080×1920 (放大 2.74×)
- **老师端 demo**：录 1920×1080 横屏 → 渲染 1920×1080 横屏
- **双端同框 demo**：用 1920×1080 横屏 / 左右分屏
- **混合输出**：如果一个视频要含双端，最终用横屏 1920×1080 比较合适

---

## 五、资源依赖清单

### 软件 / 服务（按先后顺序）
- **Node.js + npm**：Playwright + Remotion 运行时（已装）
- **FFmpeg 8.0.1**：视频转码 + 混音（已装）
- **Playwright 1.59.1**：录屏（已装）
- **Remotion 4.x**：编排（已装）
- **AI 配音 API**：ElevenLabs / Azure / 阿里云 / 火山引擎 之一（待选）
- **Rotato / AE**：用户本地软件，出 3D 翻转开场（待用户自备）

### 字体
- **思源黑体 CN（Noto Sans SC）**：中文标题 / 字幕 / 标注
- **苹方 / 微软雅黑**：备选

### 品牌资源
- 医小管 logo（高分辨率 PNG / SVG）
- 主色：紫色 `#7C3AED`（已从 student-app `pages.json` 提取）
- 配色规范文档（如果有）

### 音乐
- 无版权 BGM 一首：Epidemic Sound / Artlist / YouTube Audio Library
- 风格建议：Lo-fi / Corporate Inspirational / Tech Optimistic

---

## 六、下一步行动（待用户决策）

技术可行性的"已知部分"全部跑通，进入**脚本规划阶段**。下次讨论需要决定：

1. **脚本场景表**（按时间 | 镜头 | 旁白 | 字幕 四列写）
2. **总时长目标**（弹性，但建议先定一个数字便于规划，如 90s / 3min）
3. **学生端展示哪几个具体功能点**
4. **老师端三场景的具体演示路径**（数据大屏看哪几个数字 / 知识条目入库走哪条流程 / 实时对话演示什么问题）
5. **配音 API 选型**（先做 A/B 测试再定）
6. **资源就位**（字体 / 音乐 / logo / 配音 API key）

完成上述规划后，进入正式开干阶段，技术上没有不确定性，**就是流水线工作**：

```
脚本场景表
   ↓
分别录制 student-app / teacher-app / 双端对话 → events.json × N
   ↓
ElevenLabs 出配音 → narration.mp3
   ↓
Remotion 编排 = 视频 + zoom + 光效 + 字幕 + 配音 + BGM
   ↓
渲染 final.mp4
```

---

## 附录 A：当前 PoC 文件结构

```
yixiaoguan-v2/
├── .tmp/demo-video/                    # PoC 工程目录
│   ├── package.json                    # Playwright 依赖
│   ├── probe.mjs                       # DOM 探查脚本
│   ├── record-demo.mjs                 # 录屏 + 事件输出脚本
│   ├── out/
│   │   ├── demo.webm                   # 原始录制
│   │   ├── demo-trimmed.mp4            # trim 后干净版
│   │   ├── events.json                 # 事件 timeline
│   │   └── frames/                     # 关键 frame 截图
│   └── remotion/                       # Remotion 编排子工程
│       ├── package.json
│       ├── remotion.config.ts
│       ├── tsconfig.json
│       ├── public/demo-trimmed.mp4     # staticFile() 资源
│       ├── src/
│       │   ├── index.ts
│       │   ├── Root.tsx                # Composition 注册
│       │   ├── Composition.tsx         # zoom + pulse + label 编排
│       │   └── events.json
│       └── out/
│           └── final-v1.mp4            # 最终输出
└── video/                              # 本目录 (规划文档)
    ├── README.md
    └── 01-tech-feasibility.md          # 本文件
```

## 附录 B：PoC 渲染参数（以备参考复用）

- **Composition**: 1080×1920 @ 30fps，时长 = events.duration_ms + 1s buffer
- **背景**: `radial-gradient(ellipse at center, #1A0F3A 0%, #0F0A1F 70%, #050310 100%)`
- **视频圆角**: 40px
- **视频阴影**: `0 30px 80px rgba(124,58,237,0.35), 0 10px 30px rgba(0,0,0,0.5)`
- **基础缩放**: `BASE_SCALE = COMP_H / VIDEO_H ≈ 2.25`
- **zoom 增量**: `+0.55` (即峰值 1.55× 基础)
- **zoom 节奏**: lead 180ms → peak 320ms → hold 500ms → out 600ms
- **缓动**: cubic ease-in-out
- **光效**: 60×60 紫色 ring，0.3 → 2.5× scale，0.5s 单次扩散
- **底部 label 样式**: 毛玻璃胶囊 (`backdrop-filter: blur(20px)`)，字号 36px，圆角 999px
