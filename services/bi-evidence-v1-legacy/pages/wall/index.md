---
title: 医小管 大屏
sidebar: false
breadcrumb: false
hide_title: true
---

<script>
  let now = new Date();
  let mounted = false;
  onMount(() => {
    mounted = true;
    const t = setInterval(() => { now = new Date(); }, 1000);
    return () => clearInterval(t);
  });

  const fmt2 = (n) => String(n).padStart(2, '0');
  $: clockTime = `${fmt2(now.getHours())}:${fmt2(now.getMinutes())}:${fmt2(now.getSeconds())}`;
  $: clockDate = `${now.getFullYear()}.${fmt2(now.getMonth()+1)}.${fmt2(now.getDate())} · ${['周日','周一','周二','周三','周四','周五','周六'][now.getDay()]}`;

  const startDate = new Date('2026-05-08T00:00:00+08:00');
  $: dayNum = Math.max(1, Math.floor((now - startDate) / 86400000) + 1);
</script>

```sql kpis
select
  coalesce(sum(active_users), 0)                                                            as active,
  coalesce(sum(chat_sends), 0)                                                              as q,
  coalesce(sum(chat_ok), 0)                                                                 as a,
  case when sum(chat_sends) > 0 then round(100.0 * sum(chat_ok) / sum(chat_sends), 0) else 0 end as ai_rate,
  coalesce(sum(card_shown), 0)                                                              as blind,
  coalesce(sum(card_submitted) + sum(feedback_submitted), 0)                                as fb
from yxg.kpi_daily
```

```sql funnel
select 1 as ord, '启动 App'  as step, sum(s1_started::int)        as cnt from yxg.funnel_user
union all select 2, '浏览页面',  sum(s2_browsed::int)             from yxg.funnel_user
union all select 3, '提出问题',  sum(s3_asked::int)               from yxg.funnel_user
union all select 4, '收到回复',  sum(s4_got_answer::int)          from yxg.funnel_user
union all select 5, '触达盲区',  sum(s5_card_shown::int)          from yxg.funnel_user
union all select 6, '留下反馈',  sum(s6_gave_feedback::int)       from yxg.funnel_user
order by ord
```

```sql daily
select
  day::date as day,
  sum(chat_sends) as 提问,
  sum(chat_ok)    as AI已答,
  sum(active_users) as 活跃用户
from yxg.kpi_daily
group by 1
order by 1
```

```sql ticker
select
  strftime(client_ts, '%H:%M') as t,
  case event_name
    when 'page_view'             then '浏览'
    when 'chat_send'             then '提问'
    when 'chat_response_ok'      then 'AI 解答'
    when 'service_card_click'    then '服务跳转'
    when 'quick_question_click'  then '快捷问'
    when 'kb_doc_clicked'        then '点开文档'
    when 'unanswered_card_shown' then '盲区出现'
    when 'unanswered_user_filled' then '盲区反馈'
    when 'feedback_form_open'    then '打开反馈'
    when 'feedback_form_submit'  then '提交反馈'
    else event_name
  end as evt,
  coalesce(prop_card, prop_label, prop_path, '') as detail,
  coalesce(college_name, '') as college,
  user_type
from yxg.events_enriched
where event_name in ('chat_send', 'chat_response_ok', 'service_card_click', 'quick_question_click', 'kb_doc_clicked', 'unanswered_card_shown', 'unanswered_user_filled', 'feedback_form_submit')
order by client_ts desc
limit 20
```

<script context="module">
  // module-level helpers, no SSR conflicts
</script>

<div class="wall-root">

<!-- 顶部 status bar (极简单行) -->
<div class="wall-header">
  <div class="wall-title"><span class="accent">医小管</span>内测大屏</div>
  <div class="wall-title-meta">PILOT · VOL.I</div>
  <div class="wall-spacer"></div>
  <div class="wall-day">启动第<span class="num">{dayNum}</span>天</div>
  <div class="wall-clock">{mounted ? clockTime : '--:--:--'}<span class="wall-clock-date">{mounted ? clockDate : '----'}</span></div>
  <div class="wall-live">LIVE</div>
</div>

<!-- 6 大 KPI -->
<div class="wall-kpis">
  <div class="wall-kpi">
    <div class="wall-kpi-label">01 · Active</div>
    <div class="wall-kpi-title">活跃用户</div>
    <div class="wall-kpi-value">{kpis[0]?.active ?? 0}<span class="wall-kpi-unit">人</span></div>
  </div>
  <div class="wall-kpi">
    <div class="wall-kpi-label">02 · Questions</div>
    <div class="wall-kpi-title">累计提问</div>
    <div class="wall-kpi-value">{kpis[0]?.q ?? 0}</div>
  </div>
  <div class="wall-kpi">
    <div class="wall-kpi-label">03 · Answered</div>
    <div class="wall-kpi-title">AI 已答</div>
    <div class="wall-kpi-value">{kpis[0]?.a ?? 0}</div>
  </div>
  <div class="wall-kpi">
    <div class="wall-kpi-label">04 · AI Rate</div>
    <div class="wall-kpi-title">解答率</div>
    <div class="wall-kpi-value">{kpis[0]?.ai_rate ?? 0}<span class="wall-kpi-unit">%</span></div>
  </div>
  <div class="wall-kpi">
    <div class="wall-kpi-label">05 · Gaps</div>
    <div class="wall-kpi-title">触达盲区</div>
    <div class="wall-kpi-value">{kpis[0]?.blind ?? 0}</div>
  </div>
  <div class="wall-kpi">
    <div class="wall-kpi-label">06 · Feedback</div>
    <div class="wall-kpi-title">留下反馈</div>
    <div class="wall-kpi-value">{kpis[0]?.fb ?? 0}</div>
  </div>
</div>

<!-- 中区 漏斗 + 趋势 -->
<div class="wall-charts">

  <!-- 左：自定义漏斗 -->
  <div class="wall-card">
    <div class="wall-card-eyebrow">USER FUNNEL</div>
    <div class="wall-card-title">学生使用漏斗</div>
    <div style="margin-top:0.8rem;flex:1;">
      {#each funnel as row}
        <div class="wall-funnel-row">
          <div class="wall-funnel-step">{row.step}</div>
          <div class="wall-funnel-bar-wrap">
            <div class="wall-funnel-bar" style="width: {Math.max(2, (row.cnt / Math.max(funnel[0]?.cnt ?? 1, 1)) * 100)}%;"></div>
          </div>
          <div class="wall-funnel-num">{row.cnt}</div>
        </div>
      {/each}
    </div>
  </div>

  <!-- 右：日趋势折线 -->
  <div class="wall-card">
    <div class="wall-card-eyebrow">DAILY TREND</div>
    <div class="wall-card-title">日级提问 · AI 已答 · 活跃</div>
    <LineChart
      data={daily}
      x=day
      y={['提问', 'AI已答', '活跃用户']}
      yAxisTitle=""
      showAllXAxisLabels=true
      chartAreaHeight=260
      labelSize=11
      colorPalette={['#A78BFA', '#10B981', '#F59E0B']}
      backgroundColor="#13131A"
    />
  </div>

</div>

<!-- 底部 ticker -->
<div class="wall-ticker">
  <div class="wall-ticker-label">LIVE EVENTS</div>
  <div class="wall-ticker-track">
    {#each [...ticker, ...ticker] as e, i}
      <div class="wall-ticker-item">
        <span class="wall-ticker-time">{e.t}</span>
        <span class="wall-ticker-event">[{e.evt}]</span>
        <span class="wall-ticker-detail">{e.user_type === 'student' ? '学生' : '教师'} {e.college ? '· ' + e.college : ''} {e.detail ? '· ' + e.detail : ''}</span>
      </div>
    {/each}
    {#if ticker.length === 0}
      <div class="wall-ticker-item"><span class="wall-ticker-detail">暂无事件 · 等待学生提问</span></div>
    {/if}
  </div>
</div>

</div>
