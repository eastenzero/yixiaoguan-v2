-- ════════════════════════════════════════════════════════════════════════════
--  yixiaoguan-v2  BI 只读账号（ro_bi）
--  ──────────────────────────────────────────────────────────────────────────
--  目的：给 Evidence.dev / Metabase / Rill 等 BI 工具一个最小权限账号
--  权限：仅 SELECT public.* （含 v_* 视图），无任何写权限
--  apply 前：把 <REPLACE_ME_32_HEX> 替换为真实密码
--           生成命令：openssl rand -hex 16
--  apply: docker exec -i yx_postgres psql -U yx_admin -d yixiaoguan_v2 < this
-- ════════════════════════════════════════════════════════════════════════════

-- 创建角色（如已存在，先 DROP 再创建以确保密码刷新）
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ro_bi') THEN
    CREATE ROLE ro_bi LOGIN PASSWORD '<REPLACE_ME_32_HEX>';
  ELSE
    ALTER ROLE ro_bi WITH LOGIN PASSWORD '<REPLACE_ME_32_HEX>';
  END IF;
END
$$;

-- 数据库 + schema 连接权限
GRANT CONNECT ON DATABASE yixiaoguan_v2 TO ro_bi;
GRANT USAGE   ON SCHEMA public          TO ro_bi;

-- 表 + 序列只读
GRANT SELECT ON ALL TABLES    IN SCHEMA public TO ro_bi;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO ro_bi;

-- 未来新建的表/视图自动赋予 SELECT
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES    TO ro_bi;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO ro_bi;

-- 兜底：撤销任何写权限（PG 默认就没有，显式撤销更安心）
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM ro_bi;

-- 验证
SELECT rolname, rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, rolreplication
FROM pg_roles WHERE rolname = 'ro_bi';
