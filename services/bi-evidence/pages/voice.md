---
title: 学生声音
sidebar_position: 4
---

<div class="yxg-hero">
  <div class="yxg-eyebrow">Vol. I · Chapter 叁</div>
  <h1>学生声音</h1>
  <div class="yxg-sub">AI 答不上来的时候，他们怎么说</div>
</div>

<hr class="yxg-divider" />

<div class="yxg-quote">
我们不追求"AI 解答率 100%"。AI 答不上来时，学生愿意花 30 秒补一句"我学院 / 年级 / 类别 / 详细描述"——这才是知识库进化的真正燃料。
</div>

```sql voice_totals
select
  count(*)                                                                         as total,
  count(*) filter (where has_note)                                                 as with_note,
  count(distinct user_id)                                                          as users,
  count(*) filter (where college_id is not null)                                   as with_college,
  count(*) filter (where category is not null)                                     as with_category
from yxg.unanswered_cross
where id > 0
```

<div class="yxg-section-eyebrow">§ 1 · 反馈漏斗</div>
<div class="yxg-section-title">盲区反馈的填写完整度</div>

<Grid cols=4>
  <BigValue data={voice_totals} value=total title="总反馈数" />
  <BigValue data={voice_totals} value=with_note title="带文字说明" />
  <BigValue data={voice_totals} value=with_college title="提供学院" />
  <BigValue data={voice_totals} value=with_category title="提供类别" />
</Grid>

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 2 · 类别分布</div>
<div class="yxg-section-title">学生对自己问题的归类</div>
<p class="yxg-section-lead">奖学金、学籍、宿舍、教务……学生自选的标签反映了哪一类问题最容易让 AI 失语。</p>

```sql category_dist
select
  coalesce(category, '（未填）') as 类别,
  count(*) as 反馈数
from yxg.unanswered_cross
where id > 0
group by 1
order by 反馈数 desc
```

{#if category_dist.length > 0}
<BarChart
  data={category_dist}
  x=类别
  y=反馈数
  swapXY=true
  sort=true
  chartAreaHeight=300
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚未收到带类别的盲区反馈。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 3 · 学院分布</div>
<div class="yxg-section-title">哪些学院的学生反馈最多</div>

```sql college_dist
select
  coalesce(college_name, '（未填学院）') as 学院,
  count(*) as 反馈数
from yxg.unanswered_cross
where id > 0
group by 1
order by 反馈数 desc
limit 10
```

{#if college_dist.length > 0}
<BarChart
  data={college_dist}
  x=学院
  y=反馈数
  swapXY=true
  sort=true
  chartAreaHeight=280
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">尚未收到带学院的盲区反馈。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 4 · 最近反馈样本</div>
<div class="yxg-section-title">学生原话</div>
<p class="yxg-section-lead">最近 10 条带文字说明的盲区反馈，去除身份关联后展示。这是知识库扩充优先级最高的输入。</p>

```sql recent_notes
select
  date_trunc('day', created_at)::date as 日期,
  coalesce(college_name, '—')         as 学院,
  coalesce(grade, '—')                as 年级,
  coalesce(category, '—')             as 类别,
  user_provided_note                  as 学生原话
from yxg.unanswered_cross
where id > 0 and has_note
order by created_at desc
limit 10
```

{#if recent_notes.length > 0}
<DataTable data={recent_notes} rowShading=true />
{:else}
<p style="color:var(--hui);font-family:var(--serif);font-style:italic;">还没有学生留下文字反馈。耐心。</p>
{/if}

<hr class="yxg-divider" />

<div class="yxg-section-eyebrow">§ 5 · 反馈活跃度</div>
<div class="yxg-section-title">每日盲区反馈数</div>

```sql daily_voice
select
  day                  as 日期,
  count(*)             as 反馈数,
  count(distinct user_id) as 反馈者
from yxg.unanswered_cross
where id > 0
group by 1
order by 1
```

{#if daily_voice.length > 0}
<LineChart
  data={daily_voice}
  x=日期
  y={['反馈数', '反馈者']}
  chartAreaHeight=240
/>
{:else}
<p style="color:var(--hui);font-family:var(--serif);">数据点尚不足以画日趋势。</p>
{/if}

<div class="yxg-stamp">叁 · 完</div>
