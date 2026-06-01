---
title: 运营成本
sidebar_position: 5
---

<div class="yxg-hero">
  <div class="yxg-eyebrow">Vol. I · Chapter 肆</div>
  <h1>运营成本</h1>
  <div class="yxg-sub">每一份回答的代价 · tokens、价格、延迟、效率</div>
</div>

<hr class="yxg-divider" />

```sql cost_totals
select
  coalesce(sum(total_tokens), 0)                                                   as tokens,
  coalesce(round(sum(total_price)::numeric, 4), 0)                                 as price,
  coalesce(round(avg(latency)::numeric, 2), 0)                                     as latency_avg,
  count(*)                                                                          as calls,
  case when count(*) filter (where is_answered) > 0
       then coalesce(round(sum(total_price)::numeric / nullif(count(*) filter (where is_answered), 0), 4), 0)
       else 0 end                                                                  as cost_per_answered
from yxg.chat_enriched
where total_price is not null
```

<div class="yxg-section-eyebrow">§ 1 · 总览</div>
<div class="yxg-section-title">累计消耗 · 平均延迟</div>

<Grid cols=4>
  <BigValue data={cost_totals} value=calls title="累计调用" />
  <BigValue data={cost_totals} value=tokens title="累计 tokens" />
  <BigValue data={cost_totals} value=price title="累计费用 ¥" fmt="num4" />
  <BigValue data={cost_totals} value=latency_avg title="平均延迟 (秒)" fmt="num2" />
</Grid>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 2 · 每日趋势</div>
<div class="yxg-section-title">tokens 与费用的日级走势</div>

```sql daily_cost
select
  day_ts::date                                  as 日期,
  coalesce(sum(total_tokens), 0)                as tokens,
  coalesce(round(sum(total_price)::numeric, 4), 0) as 费用,
  count(*)                                       as 调用
from yxg.chat_enriched
where total_price is not null
group by 1
order by 1
```

{#if daily_cost.length > 0}
<LineChart
  data={daily_cost}
  x=日期
  y={['tokens', '调用']}
  yAxisTitle="次数 / tokens"
  chartAreaHeight=240
/>

<LineChart
  data={daily_cost}
  x=日期
  y=费用
  yAxisTitle="¥"
  chartAreaHeight=200
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚未有计费调用入库。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 3 · 单次问答成本</div>
<div class="yxg-section-title">每问平均消耗</div>

```sql per_call
select
  rag_bucket                                                       as RAG分桶,
  count(*)                                                          as 次数,
  coalesce(round(avg(total_tokens)::numeric, 0), 0)                 as 平均tokens,
  coalesce(round(avg(total_price)::numeric, 5), 0)                  as 平均单价,
  coalesce(round(avg(latency)::numeric, 2), 0)                      as 平均延迟
from yxg.chat_enriched
where total_tokens is not null
group by 1
order by case rag_bucket when 'high' then 1 when 'mid' then 2 when 'low' then 3 else 4 end
```

<DataTable data={per_call} rowShading=true />

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 4 · 延迟分布</div>
<div class="yxg-section-title">学生等待 AI 回复的时间</div>
<p class="yxg-section-lead">单位：秒。p95 应控制在 8s 以内，否则学生会失去耐心。</p>

```sql latency_dist
select
  case
    when latency < 1  then '< 1s'
    when latency < 3  then '1-3s'
    when latency < 6  then '3-6s'
    when latency < 10 then '6-10s'
    else '> 10s'
  end as 区间,
  count(*) as 次数
from yxg.chat_enriched
where latency is not null
group by 1
order by case
  when 区间 = '< 1s'  then 1
  when 区间 = '1-3s'  then 2
  when 区间 = '3-6s'  then 3
  when 区间 = '6-10s' then 4
  else 5
end
```

{#if latency_dist.length > 0}
<BarChart
  data={latency_dist}
  x=区间
  y=次数
  yAxisTitle="次数"
  sort=false
  chartAreaHeight=240
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚无延迟数据。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 5 · 高耗会话</div>
<div class="yxg-section-title">单次最贵 Top 10</div>

```sql top_cost
select
  conversation_id  as 会话ID,
  user_type        as 用户,
  total_tokens     as tokens,
  round(total_price::numeric, 5) as 费用,
  round(latency::numeric, 2)     as 延迟s,
  rag_bucket       as RAG,
  is_answered      as 已答
from yxg.chat_enriched
where total_price is not null
order by total_price desc nulls last
limit 10
```

<DataTable data={top_cost} rowShading=true />

<div class="yxg-stamp">肆 · 完</div>
