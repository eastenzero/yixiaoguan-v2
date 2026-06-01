# Prompt：医小管演示视频 · Intro 片头素材搜索

> 派单创建：2026-05-11 晚 · Cascade 导演产出
> 上游剧本契约：`@F:\Documents\code\yixiaoguan-v2\video\04-script-plan.md` §2.1 Intro

---

## 你的任务（一句话）

为医小管产品演示长片找一段 **5-8 秒 1920×1080+ 30fps 免费商用** 的 stock 视频，作为开场片头使用。

---

## 项目背景

医小管 = **中国大学校园 AI 问答助手**（学生提问 → AI 流式回答 → 复杂问题转人工老师接单）。当前在做产品演示长片（4-5 分钟），结构如下：

```
[Intro 5-8s] ← 你要找的 ← stock 片头
[AE iPhone 转场 30s] ← 紫色 royal blue 背景，4 个无 logo iPhone 镜头串烧
[D1 学生端 70s] [D2 教师端 70s] [D3 双端实时分屏 50s] [Outro 10s]
```

**主色**：`#7C3AED` 紫
**AE 段背景色**：Dark Royal Blue（深皇家蓝）
**整片输出**：1920×1080 横屏 30fps H.264

---

## 必须满足的规格

| 项           | 要求                                                                        |
| ------------ | --------------------------------------------------------------------------- |
| 可用片段长度 | 5-8 秒（视频本身更长也行，能裁出这一段就够）                                |
| 分辨率       | 至少 1920×1080，4K 最佳（4K 给后期裁剪余地）                               |
| 帧率         | **30 或 60 fps**（24fps 不要，跟主合成不匹配）                        |
| 授权         | **免费商用**：CC0 / Pexels License / Pixabay License / Mixkit License |
| 容器         | mp4 (H.264) 优先；webm 也可接受                                             |
| 文件大小     | < 200 MB（5-8s 片段一般 30-100 MB）                                         |

---

## 风格优先级（必须按这个顺序找）

### 🥇 首选：紫色科技感粒子 / 抽象数字网络

- 关键词：`purple particle network`, `digital connection`, `abstract tech background`, `purple gradient motion`, `light streaks purple`, `data flow purple`, `cyber background purple`
- 理由：呼应主色 + AE 段背景顺接 + AI 智能主题不言自明

### 🥈 备选 1：抽象几何动画 / 紫色光线流动

- 关键词：`abstract geometric loop`, `purple light streaks`, `holographic background`, `motion graphics purple`, `glowing lines abstract`

### 🥉 备选 2：校园航拍（仅在 1+2 找不到合适时启用）

- 关键词：`university campus aerial`, `college campus drone`, `chinese university`, `campus walking shot`

---

## 严格不要

- ❌ 有水印 / logo / 字幕的
- ❌ 有面孔正脸特写（隐私 + 版权风险）
- ❌ 含具体品牌 / 学校 / 商业 logo 的
- ❌ 24fps 的（重采样到 30fps 会糊或抖）
- ❌ 低于 1080p 的
- ❌ 节奏混乱、闪烁过快可能引起不适的
- ❌ 主色调跟 #7C3AED 紫色严重冲突的（大红、大黄、明亮橙背景）
- ❌ "看着假"的低质量 / 素人手机拍摄的素材

---

## 搜索站点（按优先级）

| # | 站点                                | 备注                                     |
| - | ----------------------------------- | ---------------------------------------- |
| 1 | https://www.pexels.com/videos/      | **首选**，质量稳定，下载直接给 mp4 |
| 2 | https://pixabay.com/videos/         | 备选，免费商用                           |
| 3 | https://mixkit.co/free-stock-video/ | 备选，分类清晰                           |
| 4 | https://coverr.co/                  | 备选                                     |
| 5 | https://www.videvo.net/             | 部分免费，注意分辨 license               |

---

## 操作方法（双路径，按你的能力选）

### 路线 A：你能跑 Playwright（推荐）

主仓的 `.tmp/demo-video/` 已经装好 Playwright，可直接用：

```js
// .tmp/demo-video/search-intro.mjs
import { chromium } from 'playwright';
import fs from 'fs';

const KEYWORDS = [
  'purple particle network',
  'digital connection abstract',
  'tech background purple',
  'abstract geometric loop',
  'purple light streaks',
];

const browser = await chromium.launch({ headless: false });
const page = await browser.newPage();

const results = [];
for (const kw of KEYWORDS) {
  console.log(`Searching: ${kw}`);
  await page.goto(`https://www.pexels.com/search/videos/${encodeURIComponent(kw)}/`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1500);

  const cards = await page.$$eval('a[href*="/video/"]', (links) => {
    const seen = new Set();
    return links
      .filter((a) => {
        const href = a.href;
        if (seen.has(href)) return false;
        seen.add(href);
        return true;
      })
      .slice(0, 10)
      .map((a) => ({
        href: a.href,
        thumb: a.querySelector('img')?.src,
        alt: a.querySelector('img')?.alt,
      }));
  });
  results.push({ keyword: kw, count: cards.length, cards });
}

fs.writeFileSync('intro-candidates.json', JSON.stringify(results, null, 2));
console.log(`Saved ${results.reduce((sum, r) => sum + r.count, 0)} candidates`);
await browser.close();
```

跑完后 `intro-candidates.json` 会有 50 个候选。**你需要进一步**：

1. 打开每个 `href` 看时长、分辨率、是否有水印
2. 筛掉不符合规格的
3. 输出 Top 10 报告（见下方"输出格式"）
4. 如果 Pexels 候选不够，对 Pixabay/Mixkit 重复同样流程（DOM selector 不同）

### 路线 B：你只有浏览器/网页搜索能力

按上面的关键词，逐个站点搜索，每个站点挑前 10 个候选，人工核对：

- 时长够不够 5-8s
- 分辨率 ≥ 1080p
- 帧率（页面通常会显示）
- 授权（页面会标注 license）

---

## 输出格式（必须返回这个）

把结果整理成 markdown 报告，结构：

```markdown
## 候选 Top 10

| # | 站点 | 标题 | 时长 | 分辨率/fps | 授权 | 直链 | 简评 |
|---|---|---|---|---|---|---|---|
| 1 | Pexels | Purple Particle Network | 0:32 | 4K/30 | Pexels | https://www.pexels.com/video/... | 紫色饱和度好，前 5-8s 流速合适，无水印 |
| 2 | Pixabay | Abstract Tech Loop | 0:15 | 1080p/60 | Pixabay | https://... | 几何线条，节奏稍快，可裁前 6s |
| ... | ... | ... | ... | ... | ... | ... | ... |

## 推荐 Top 3（按从高到低）

### 1. [Pexels - Purple Particle Network](https://...)
- **优点**：紫色饱和度跟主色 #7C3AED 几乎一致；30fps 免转码；4K 给后期留余地；前 8s 节奏稳定不抢戏
- **缺点**：粒子密度略高，可能跟 logo 入场叠加时不清爽
- **裁剪建议**：取 0:08-0:14 或 0:20-0:26 这段相对干净的区间

### 2. ...
### 3. ...

## 下载方式备注
- Pexels：登录后 "Free Download" 按钮直接给 mp4
- Pixabay：右上角 "Free Download" → 选 1080p / 4K
- Mixkit：直接 "Download free" 按钮

## 我的整体观察
（一两句话总结找的过程中的发现，比如"紫色科技粒子素材在 Pexels 上很多但大部分 24fps，最终筛出 6 个 30fps 的；建议候选 1"）
```

---

## 验收标准

用户拿到你的报告后，会做以下事情：

1. 点开你列的 Top 3 链接预览
2. 选 1 个最终方案
3. 下载 mp4 → 放到 `F:\Documents\code\yixiaoguan-v2\.tmp\demo-video\intro\` 目录

所以你的报告必须满足：

- ✅ 所有链接**真实可访问**（不要捏造，不要瞎写）
- ✅ 所有授权信息**正确**（页面上确认过）
- ✅ Top 3 推荐**有理有据**，不是随机挑
- ✅ 至少 1 个候选满足"30fps + 1080p+ + 紫色调 + 免费商用"全部硬条件

---

## 加分项（可选）

如果你能直接下载，把 Top 3 各下载 1 份到 `.tmp/demo-video/intro-candidates/` 目录，用 `01-pexels-particle.mp4` / `02-pixabay-tech.mp4` / `03-mixkit-glow.mp4` 编号命名，用户可以直接拖到播放器预览选最终版。这能省用户 5 分钟。

---

## 完成后下一步

报告交回后，用户人工挑选 1 个 → 下载 → 进入 Phase 1 总编排时由 Remotion `<Sequence>` 嵌入开场。
