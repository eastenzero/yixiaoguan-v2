---
title: 数据总览
sidebar_position: 2
---

<div class="yxg-hero">
  <div class="yxg-eyebrow">Vol. I · Chapter 壹</div>
  <h1>数据总览</h1>
  <div class="yxg-sub">从打开 App 到留下反馈，六步路径上每一处的留存与流失</div>
</div>

<hr class="yxg-divider" />

```sql totals
select
  coalesce(sum(active_users), 0)                                                            as active,
  coalesce(sum(pv), 0)                                                                      as pv,
  coalesce(sum(chat_sends), 0)                                                              as q,
  coalesce(sum(chat_ok), 0)                                                                 as a,
  case when sum(chat_sends) > 0 then round(100.0 * sum(chat_ok) / sum(chat_sends), 1) else 0 end as ai_rate,
  coalesce(sum(card_shown), 0)                                                              as blind,
  coalesce(sum(card_submitted) + sum(feedback_submitted), 0)                                as fb
from yxg.kpi_daily
```

<div class="yxg-section-eyebrow">§ 1 · 核心指标</div>
<div class="yxg-section-title">六个值得关注的数字</div>

<Grid cols=3>
  <BigValue data={totals} value=active title="活跃用户" />
  <BigValue data={totals} value=q title="累计提问" />
  <BigValue data={totals} value=ai_rate title="AI 解答率" fmt="0.0\%" />
  <BigValue data={totals} value=pv title="累计浏览" />
  <BigValue data={totals} value=blind title="触达盲区" />
  <BigValue data={totals} value=fb title="留下反馈" />
</Grid>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 2 · 学生使用漏斗</div>
<div class="yxg-section-title">从启动 App 到留下反馈</div>
<p class="yxg-section-lead">六步路径每一步的用户人数。每一格的"窄"都是一次留住学生的失败。</p>

```sql funnel
select 1 as ord, '① 启动 App'  as step, sum(s1_started::int)        as cnt from yxg.funnel_user
union all select 2, '② 浏览页面',  sum(s2_browsed::int)             from yxg.funnel_user
union all select 3, '③ 提出问题',  sum(s3_asked::int)               from yxg.funnel_user
union all select 4, '④ 收到回复',  sum(s4_got_answer::int)          from yxg.funnel_user
union all select 5, '⑤ 触达盲区',  sum(s5_card_shown::int)          from yxg.funnel_user
union all select 6, '⑥ 留下反馈',  sum(s6_gave_feedback::int)       from yxg.funnel_user
order by ord
```

<BarChart
  data={funnel}
  x=step
  y=cnt
  swapXY=true
  yAxisTitle="用户数"
  sort=false
  chartAreaHeight=320
/>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 3 · 日维度</div>
<div class="yxg-section-title">每日提问与解答趋势</div>

```sql daily
select
  day::date as day,
  sum(active_users) as 活跃,
  sum(chat_sends)   as 提问,
  sum(chat_ok)      as 已答
from yxg.kpi_daily
group by 1
order by 1
```

<LineChart
  data={daily}
  x=day
  y={['活跃', '提问', '已答']}
  yAxisTitle="次数"
  showAllXAxisLabels=true
  chartAreaHeight=260
/>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 4 · 时段热力</div>
<div class="yxg-section-title">学生在哪些时段最活跃</div>
<p class="yxg-section-lead">7 天 × 24 小时的页面浏览热力图，暴露学生真实的使用窗口。</p>

```sql heatmap
select
  case dow
    when 0 then '周日' when 1 then '周一' when 2 then '周二' when 3 then '周三'
    when 4 then '周四' when 5 then '周五' when 6 then '周六'
  end as dow_label,
  hod as hour,
  count(*) as cnt
from yxg.events_enriched
where event_name = 'page_view'
group by 1, 2
order by 2
```

{#if heatmap.length > 0}
<Heatmap
  data={heatmap}
  x=hour
  y=dow_label
  value=cnt
  yAxisTitle=""
  xAxisTitle="小时"
  chartAreaHeight=240
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">数据量尚不足以铺成热力图，再观察几天。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 5 · 数据回执</div>
<div class="yxg-section-title">日级 KPI 抽样</div>

```sql kpi_table
select
  day::date    as 日期,
  user_type    as 用户类型,
  active_users as 活跃,
  pv           as 浏览,
  chat_sends   as 提问,
  chat_ok      as 已答,
  card_shown   as 盲区,
  feedback_submitted + card_submitted as 反馈
from yxg.kpi_daily
order by day desc, user_type
```

<DataTable data={kpi_table} rowShading=true />

<div class="yxg-stamp">壹 · 完</div>
