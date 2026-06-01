-- ════════════════════════════════════════════════════════════════════════════
--  yixiaoguan-v2  BI 语义层 VIEW（Evidence.dev / 任意 BI 工具消费）
--  ──────────────────────────────────────────────────────────────────────────
--  目的：把业务表打平 + join 维度，让 BI 工具可以零 SQL 拼接画图。
--  apply: docker exec -i yx_postgres psql -U yx_admin -d yixiaoguan_v2 < this
--  幂等:  全部 CREATE OR REPLACE，可反复执行
--  设计:  详见 .tasks/bi-evidence-design-20260509.md §2
-- ════════════════════════════════════════════════════════════════════════════


-- ─── 1. 用户维度 ────────────────────────────────────────────────────────────
-- staff_id LIKE 'pilot:%' 是内测匿名用户的 sentinel（详见 r11-pilot-tables migration）
CREATE OR REPLACE VIEW v_users_dim AS
SELECT
  u.id,
  u.staff_id,
  u.name,
  u.role::text                                                        AS role,
  u.college_id,
  c.name                                                              AS college_name,
  c.campus,
  u.class_id,
  cls.name                                                            AS class_name,
  cls.grade_year,
  (u.staff_id LIKE 'pilot:%')                                         AS is_pilot,
  CASE WHEN u.staff_id LIKE 'pilot:%' THEN 'pilot' ELSE 'real' END    AS user_type,
  u.is_active,
  u.created_at                                                        AS joined_at
FROM users u
LEFT JOIN colleges c   ON c.id   = u.college_id
LEFT JOIN classes  cls ON cls.id = u.class_id;

COMMENT ON VIEW v_users_dim IS 'BI 用户维度：pilot/real 标签 + 学院/班级/校区/年级 一站式 join';


-- ─── 2. events 一站式视图 ──────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_events_enriched AS
SELECT
  e.id,
  e.event_name,
  e.props,
  e.client_ts,
  e.created_at,
  e.user_id,
  d.staff_id,
  d.is_pilot,
  d.user_type,
  d.college_id,
  d.college_name,
  d.campus,
  d.class_id,
  d.class_name,
  d.grade_year,
  date_trunc('day',  e.created_at)::date    AS day_ts,
  date_trunc('hour', e.created_at)          AS hour_ts,
  EXTRACT(dow  FROM e.created_at)::int      AS dow,
  EXTRACT(hour FROM e.created_at)::int      AS hod
FROM events e
LEFT JOIN v_users_dim d ON d.id = e.user_id;

COMMENT ON VIEW v_events_enriched IS 'events + 用户维度，BI 工具直接消费';


-- ─── 3. chat_analytics 一站式视图 ──────────────────────────────────────────
CREATE OR REPLACE VIEW v_chat_enriched AS
SELECT
  ca.id,
  ca.conversation_id,
  ca.user_id,
  ca.user_query,
  ca.query_norm,
  ca.rag_score,
  ca.kb_doc_matched,
  ca.is_answered,
  ca.prompt_tokens,
  ca.completion_tokens,
  ca.total_tokens,
  ca.prompt_price,
  ca.completion_price,
  ca.total_price,
  ca.currency,
  ca.latency,
  ca.created_at,
  d.staff_id,
  d.is_pilot,
  d.user_type,
  d.college_name,
  d.class_name,
  d.grade_year,
  d.campus,
  date_trunc('day', ca.created_at)::date    AS day_ts,
  CASE
    WHEN ca.rag_score IS NULL THEN 'unknown'
    WHEN ca.rag_score < 0.3   THEN 'low'
    WHEN ca.rag_score < 0.6   THEN 'mid'
    ELSE                           'high'
  END                                       AS rag_bucket
FROM chat_analytics ca
LEFT JOIN v_users_dim d ON d.id = ca.user_id;

COMMENT ON VIEW v_chat_enriched IS 'chat_analytics + 用户维度 + RAG 分桶 + 日聚合键';


-- ─── 4. 日级 KPI rollup ───────────────────────────────────────────────────
-- 一行 = 一个 (day, user_type) 组合，BI 工具直接做趋势线 / 求和卡片
CREATE OR REPLACE VIEW v_kpi_daily AS
SELECT
  date_trunc('day', e.created_at)::date AS day,
  COALESCE(d.user_type, 'unknown')      AS user_type,
  COUNT(DISTINCT e.user_id) FILTER (WHERE e.event_name='app_start')                   AS dau,
  COUNT(DISTINCT e.user_id)                                                           AS active_users,
  COUNT(*) FILTER (WHERE e.event_name='page_view')                                    AS pv,
  COUNT(*) FILTER (WHERE e.event_name='chat_send')                                    AS chat_sends,
  COUNT(*) FILTER (WHERE e.event_name='chat_response_ok')                             AS chat_ok,
  COUNT(*) FILTER (WHERE e.event_name='chat_response_error')                          AS chat_err,
  COUNT(*) FILTER (WHERE e.event_name='unanswered_card_shown')                        AS card_shown,
  COUNT(*) FILTER (WHERE e.event_name='unanswered_card_submitted')                    AS card_submitted,
  COUNT(*) FILTER (WHERE e.event_name='unanswered_card_dismissed')                    AS card_dismissed,
  COUNT(*) FILTER (WHERE e.event_name='feedback_form_open')                           AS feedback_opens,
  COUNT(*) FILTER (WHERE e.event_name='feedback_form_submit')                         AS feedback_submitted,
  COUNT(*) FILTER (WHERE e.event_name='kb_doc_clicked')                               AS kb_clicks,
  COUNT(*) FILTER (WHERE e.event_name='service_card_click')                           AS service_clicks,
  COUNT(*) FILTER (WHERE e.event_name='quick_question_click')                         AS quick_clicks
FROM events e
LEFT JOIN v_users_dim d ON d.id = e.user_id
GROUP BY 1, 2;

COMMENT ON VIEW v_kpi_daily IS '日级 KPI rollup，按 user_type 切分';


-- ─── 5. 用户级漏斗（每用户最远到达的步骤） ─────────────────────────────────
CREATE OR REPLACE VIEW v_funnel_user AS
WITH per_user AS (
  SELECT
    e.user_id,
    bool_or(e.event_name = 'app_start')                                              AS s1_started,
    bool_or(e.event_name = 'page_view')                                              AS s2_browsed,
    bool_or(e.event_name = 'chat_send')                                              AS s3_asked,
    bool_or(e.event_name = 'chat_response_ok')                                       AS s4_got_answer,
    bool_or(e.event_name = 'unanswered_card_shown')                                  AS s5_card_shown,
    bool_or(e.event_name IN ('unanswered_card_submitted','feedback_form_submit'))   AS s6_gave_feedback
  FROM events e
  WHERE e.user_id IS NOT NULL
  GROUP BY 1
)
SELECT
  pu.user_id,
  pu.s1_started,
  pu.s2_browsed,
  pu.s3_asked,
  pu.s4_got_answer,
  pu.s5_card_shown,
  pu.s6_gave_feedback,
  d.user_type,
  d.college_name,
  d.campus,
  d.class_name,
  d.grade_year
FROM per_user pu
LEFT JOIN v_users_dim d ON d.id = pu.user_id;

COMMENT ON VIEW v_funnel_user IS '每用户漏斗推进位置（6 步），SUM(::int) 即各步用户数';


-- ─── 6. 服务/快捷问热度 ────────────────────────────────────────────────────
-- service_card_click(props.card, props.source) + quick_question_click(props.label) 统一形态
CREATE OR REPLACE VIEW v_service_heat AS
SELECT
  e.event_name,
  COALESCE(e.props->>'card', e.props->>'label')                                       AS item,
  e.props->>'source'                                                                  AS source,
  d.user_type,
  COUNT(*)                                                                            AS clicks,
  COUNT(DISTINCT e.user_id)                                                           AS users,
  date_trunc('day', e.created_at)::date                                               AS day
FROM events e
LEFT JOIN v_users_dim d ON d.id = e.user_id
WHERE e.event_name IN ('service_card_click', 'quick_question_click')
GROUP BY 1, 2, 3, 4, 7;

COMMENT ON VIEW v_service_heat IS '服务卡 + 快捷问点击聚合（按 item × source × user_type × day）';


-- ─── 7. 未答反馈交叉视图 ───────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_unanswered_cross AS
SELECT
  uuf.id,
  uuf.user_id,
  d.user_type,
  uuf.user_provided_college_id                                                        AS college_id,
  c.name                                                                              AS college_name,
  uuf.user_provided_grade                                                             AS grade,
  uuf.user_provided_category                                                          AS category,
  uuf.user_provided_note,
  (uuf.user_provided_note IS NOT NULL AND length(trim(uuf.user_provided_note)) > 0)   AS has_note,
  uuf.created_at,
  date_trunc('day', uuf.created_at)::date                                             AS day
FROM unanswered_user_feedback uuf
LEFT JOIN v_users_dim d ON d.id = uuf.user_id
LEFT JOIN colleges    c ON c.id = uuf.user_provided_college_id;

COMMENT ON VIEW v_unanswered_cross IS '盲区反馈交叉表：学院 × 年级 × 类别 × note';
