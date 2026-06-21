-- Evidence v40 在空表写 parquet 时会产出 truncated 文件导致 build 失败。
-- 工作绕：当 v_unanswered_cross 为空时输出 1 行 has_note=false 的 dummy，
-- 真实数据出现后该 dummy 自动消失。前端通过 `where id is not null` 过滤。
WITH src AS (
  SELECT * FROM v_unanswered_cross
),
fallback AS (
  -- 用 epoch 0 而非 NULL，避免 Evidence sources 把"全 NULL 列"
  -- 推断为 Float64 后续 date_trunc 报错
  SELECT
    -1::int                                AS id,
    -1::int                                AS user_id,
    'placeholder'::text                    AS user_type,
    NULL::int                              AS college_id,
    NULL::text                             AS college_name,
    NULL::text                             AS grade,
    NULL::text                             AS category,
    NULL::text                             AS user_provided_note,
    false                                  AS has_note,
    '1970-01-01 00:00:00+00'::timestamptz  AS created_at,
    '1970-01-01'::date                     AS day
  WHERE NOT EXISTS (SELECT 1 FROM src)
)
SELECT * FROM src
UNION ALL
SELECT * FROM fallback

