#!/usr/bin/env bash
PGPASSWORD=f0263944224d4b2470a57bb788d87f4a psql -h 127.0.0.1 -U ro_bi -d yixiaoguan_v2 <<'SQL'
-- 看 client_ts 和 created_at 的原始值 + 各种时区转换
SELECT
  event_name,
  client_ts                                                      AS raw_client_ts,
  created_at                                                     AS raw_created_at,
  to_char(client_ts,                                    'HH24:MI') AS as_is,
  to_char(client_ts AT TIME ZONE 'Asia/Shanghai',       'HH24:MI') AS tz_shanghai,
  to_char(client_ts AT TIME ZONE 'UTC',                 'HH24:MI') AS tz_utc,
  to_char((client_ts AT TIME ZONE 'UTC') AT TIME ZONE 'Asia/Shanghai', 'HH24:MI') AS utc_to_sh
FROM v_events_enriched
ORDER BY client_ts DESC
LIMIT 6;

-- 服务器本身时区
SHOW timezone;
SELECT now(), current_timestamp, timezone('Asia/Shanghai', now());
SQL
