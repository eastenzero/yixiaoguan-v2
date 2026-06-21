SELECT
  id, event_name, client_ts, created_at,
  user_id, staff_id, is_pilot, user_type,
  college_id, college_name, campus,
  class_id, class_name, grade_year,
  day_ts, hour_ts, dow, hod,
  props->>'card'   AS prop_card,
  props->>'label'  AS prop_label,
  props->>'source' AS prop_source,
  props->>'path'   AS prop_path,
  (props->>'content_length')::int AS prop_content_length
FROM v_events_enriched
