#!/usr/bin/env bash
# 探 v_events_enriched 的 props jsonb 实际结构
PGPASSWORD=f0263944224d4b2470a57bb788d87f4a psql -h 127.0.0.1 -U ro_bi -d yixiaoguan_v2 <<'SQL'
-- 各事件 props 示例
select event_name, props
from v_events_enriched
where event_name in ('chat_send', 'chat_response_ok', 'service_card_click', 'quick_question_click', 'kb_doc_clicked', 'unanswered_card_shown', 'unanswered_user_filled', 'feedback_form_submit', 'page_view')
order by client_ts desc
limit 12;

-- 看 v_kpi_daily 最近几天
select * from v_kpi_daily order by day desc limit 10;

-- 漏斗 sanity
select
  count(*) as total,
  sum(s1_started::int) s1,
  sum(s2_browsed::int) s2,
  sum(s3_asked::int)   s3,
  sum(s4_got_answer::int) s4,
  sum(s5_card_shown::int) s5,
  sum(s6_gave_feedback::int) s6
from v_funnel_user
where user_type = 'student';
SQL
