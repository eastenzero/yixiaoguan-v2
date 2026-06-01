#!/usr/bin/env bash
PGPASSWORD=f0263944224d4b2470a57bb788d87f4a psql -h 127.0.0.1 -U ro_bi -d yixiaoguan_v2 <<'SQL'
-- user_type 的取值域
select distinct user_type from v_events_enriched;
select distinct user_type, count(*) from v_funnel_user group by 1;

-- 非 page_view 事件的 props 示例
select event_name, props
from v_events_enriched
where event_name != 'page_view'
order by client_ts desc
limit 20;

-- 事件类型分布
select event_name, count(*) cnt
from v_events_enriched
group by 1
order by 2 desc;

-- funnel 在 pilot 下
select
  count(*) total,
  sum(s1_started::int) s1,
  sum(s2_browsed::int) s2,
  sum(s3_asked::int)   s3,
  sum(s4_got_answer::int) s4,
  sum(s5_card_shown::int) s5,
  sum(s6_gave_feedback::int) s6
from v_funnel_user
where user_type = 'pilot';
SQL
