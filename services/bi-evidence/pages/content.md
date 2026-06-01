---
title: 内容热度
sidebar_position: 3
---

<div class="yxg-hero">
  <div class="yxg-eyebrow">Vol. I · Chapter 贰</div>
  <h1>内容热度</h1>
  <div class="yxg-sub">学生最关心什么主题——服务卡、快捷问、知识库文档</div>
</div>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 1 · 服务卡 Top</div>
<div class="yxg-section-title">首页服务入口被点击次数</div>
<p class="yxg-section-lead">学生从首页/服务页跳转到外链（校园网、电费、宿舍等）的次数。点击越多说明该服务的"找入口"需求越频繁。</p>

```sql service_top
select
  item                      as 服务,
  coalesce(source, '未标')  as 来源,
  sum(clicks)               as 点击,
  sum(users)                as 用户
from yxg.service_heat
where event_name = 'service_card_click'
group by 1, 2
order by 点击 desc
limit 10
```

{#if service_top.length > 0}
<BarChart
  data={service_top}
  x=服务
  y=点击
  swapXY=true
  sort=true
  chartAreaHeight=320
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚无服务卡点击数据。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 2 · 快捷问 Top</div>
<div class="yxg-section-title">首页推荐问题被选用的频次</div>
<p class="yxg-section-lead">学生从首页"快捷问"标签直接跳到聊天的次数。这一栏的高频项就是首页推荐位的最优 candidate。</p>

```sql quick_top
select
  item        as 问题,
  sum(clicks) as 点击,
  sum(users)  as 用户
from yxg.service_heat
where event_name = 'quick_question_click'
group by 1
order by 点击 desc
limit 10
```

{#if quick_top.length > 0}
<BarChart
  data={quick_top}
  x=问题
  y=点击
  swapXY=true
  sort=true
  chartAreaHeight=280
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚无快捷问点击数据。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 3 · KB 文档命中</div>
<div class="yxg-section-title">RAG 知识库哪些文档最常被召回</div>
<p class="yxg-section-lead">每次 AI 回答时 RAG 检索到的 top-1 命中文档名。这张表是知识库内容运营的"销量榜"——出现频次高的文档值得优先精修。</p>

```sql kb_hit
select
  coalesce(kb_doc_matched, '（未命中）') as 命中文档,
  count(*)                                as 引用次数,
  round(avg(rag_score)::numeric, 3)       as 平均分,
  count(distinct user_id)                 as 涉及用户
from yxg.chat_enriched
group by 1
order by 引用次数 desc
limit 15
```

<DataTable data={kb_hit} rowShading=true />

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 4 · KB 召回质量分桶</div>
<div class="yxg-section-title">RAG score 分布</div>
<p class="yxg-section-lead">每条 AI 问答的 RAG 召回分数分桶。high (≥0.6) 比例越高越说明知识库覆盖到位。</p>

```sql rag_bucket
select
  rag_bucket,
  count(*) as cnt
from yxg.chat_enriched
group by 1
order by case rag_bucket
  when 'high'    then 1
  when 'mid'     then 2
  when 'low'     then 3
  when 'unknown' then 4
end
```

<BarChart
  data={rag_bucket}
  x=rag_bucket
  y=cnt
  yAxisTitle="次数"
  chartAreaHeight=240
/>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 5 · 文档点开行为</div>
<div class="yxg-section-title">学生主动点开"参考资料"的次数</div>

```sql doc_clicks
select
  date_trunc('day', created_at)::date as 日期,
  count(*) as 点开次数,
  count(distinct user_id) as 涉及用户
from yxg.events_enriched
where event_name = 'kb_doc_clicked'
group by 1
order by 1
```

{#if doc_clicks.length > 0}
<LineChart
  data={doc_clicks}
  x=日期
  y={['点开次数', '涉及用户']}
  chartAreaHeight=240
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚无文档点开数据。</p>
{/if}

<div class="yxg-stamp">贰 · 完</div>
