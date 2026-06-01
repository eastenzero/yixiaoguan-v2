---
title: 医小管 · 内测特刊
hide_title: true
sidebar_position: 1
---

<div class="yxg-hero">
  <div class="yxg-eyebrow">PILOT · VOL. I · 山一医</div>
  <h1>医小管<br/>内测特刊</h1>
  <div class="yxg-sub">校园智能助理 · 第一阶段数据观察</div>
  <div class="yxg-meta">启于 <strong>2026-05-08</strong> · 公共事业管理 2025-1 班</div>
</div>

<div class="yxg-quote">
"AI 不只是回答，而是在听学生说话。这一期记录我们听到的每一句、每一次点击、每一份反馈。"
</div>

```sql totals
select
  coalesce(sum(chat_sends), 0)        as questions,
  coalesce(sum(chat_ok), 0)           as answered,
  coalesce(sum(active_users), 0)      as users,
  coalesce(sum(card_shown), 0)        as blind_spots
from yxg.kpi_daily
```

<div class="yxg-section-eyebrow">I · 一周观测</div>
<div class="yxg-section-title">第一阶段累计</div>

<Grid cols=4>
  <BigValue data={totals} value=questions title="累计提问" />
  <BigValue data={totals} value=answered title="AI 已答" />
  <BigValue data={totals} value=users title="活跃用户" />
  <BigValue data={totals} value=blind_spots title="触达盲区" />
</Grid>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">II · 内容章节</div>
<div class="yxg-section-title">本期目录</div>

<Grid cols=2>

  <div>
    <h3 style="font-family:var(--serif);color:var(--jiang);margin:0 0 0.4rem;font-size:1.2rem;font-weight:700;">壹 · 数据总览</h3>
    <p style="font-family:var(--serif);color:var(--hui);margin:0 0 0.5rem;line-height:1.7;">核心 KPI 与漏斗：从打开 App 到留下反馈的六步路径，每一步留下多少人。</p>
    <a href="/bi/overview">阅读 →</a>
  </div>

  <div>
    <h3 style="font-family:var(--serif);color:var(--jiang);margin:0 0 0.4rem;font-size:1.2rem;font-weight:700;">贰 · 内容热度</h3>
    <p style="font-family:var(--serif);color:var(--hui);margin:0 0 0.5rem;line-height:1.7;">服务卡片点击、快捷问选择、知识库文档命中——学生最关心什么主题。</p>
    <a href="/bi/content">阅读 →</a>
  </div>

  <div>
    <h3 style="font-family:var(--serif);color:var(--jiang);margin:0 0 0.4rem;font-size:1.2rem;font-weight:700;">叁 · 学生声音</h3>
    <p style="font-family:var(--serif);color:var(--hui);margin:0 0 0.5rem;line-height:1.7;">盲区反馈交叉、未答问题分布、通用反馈——AI 答不上来的时候，他们怎么说。</p>
    <a href="/bi/voice">阅读 →</a>
  </div>

  <div>
    <h3 style="font-family:var(--serif);color:var(--jiang);margin:0 0 0.4rem;font-size:1.2rem;font-weight:700;">肆 · 运营成本</h3>
    <p style="font-family:var(--serif);color:var(--hui);margin:0 0 0.5rem;line-height:1.7;">tokens 消耗与价格趋势，每一份回答的成本，AI 解答率与单位成本的权衡。</p>
    <a href="/bi/cost">阅读 →</a>
  </div>

</Grid>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">III · 卷尾</div>
<div class="yxg-section-title">编辑手记</div>

<div style="font-family:var(--serif);color:var(--mohei);line-height:1.85;font-size:1.05rem;max-width:62ch;">

本期数据仅来自首批内测用户，规模小，趋势线尚不平滑。但每一个数字背后都是一次真实的提问、一次具体的困惑、一次微小的尝试。

我们不追求"今日提问破百"的烟花式增长。我们追求的是 AI 能否在学生最需要的时候说一句真正帮上忙的话——AI 答出而不空、答错而能感知、答不上而能转交辅导员。

这份特刊不是给数字看的，是给那些试图让 AI 真正落地校园的人看的。

</div>

<div class="yxg-stamp">医小管编辑部 · 2026</div>
