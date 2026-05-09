#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 C2 · restore yxg_v2.dump 到 yx_postgres
# 前置:dump 已 scp 到 /tmp/yxg_v2.dump
#
# 用法:YXG_PASS=<ub 上 yxg user 密码> bash 03c-pg-restore.sh
# YXG_PASS 来源:从 ub 的 services/gateway/.env database_url 中提取
#   ssh ub "grep ^database_url= dev/yixiaoguan-v2/services/gateway/.env"
#   格式 postgresql+asyncpg://yxg:<PASS>@localhost:5432/...

set -e

if [ -z "${YXG_PASS:-}" ]; then
  echo "[ERR] 必须传 YXG_PASS=<ub-yxg-password>; 从 ub 的 gateway .env 中提取"
  echo "      ssh ub \"grep ^database_url= dev/yixiaoguan-v2/services/gateway/.env\""
  exit 1
fi

echo "=== 1) 拷贝 dump 到容器内 ==="
docker cp /tmp/yxg_v2.dump yx_postgres:/tmp/yxg_v2.dump

echo "=== 2) 建 yxg user ==="
exists=$(docker exec yx_postgres psql -U yx_admin -d postgres -tA -c "SELECT 1 FROM pg_roles WHERE rolname='yxg'")
if [ "$exists" = "1" ]; then
  echo "yxg already exists"
else
  docker exec yx_postgres psql -U yx_admin -d postgres -c "CREATE USER yxg WITH PASSWORD '${YXG_PASS}';"
fi

echo "=== 3) 建库 ==="
exists=$(docker exec yx_postgres psql -U yx_admin -d postgres -tA -c "SELECT 1 FROM pg_database WHERE datname='yixiaoguan_v2'")
if [ "$exists" = "1" ]; then
  echo "yixiaoguan_v2 already exists"
else
  docker exec yx_postgres psql -U yx_admin -d postgres -c "CREATE DATABASE yixiaoguan_v2 OWNER yxg;"
fi

echo "=== 4) restore (no-owner --role=yxg) ==="
docker exec yx_postgres pg_restore -U yx_admin -d yixiaoguan_v2 --no-owner --role=yxg /tmp/yxg_v2.dump 2>&1 | tail -15 || echo "[WARN] pg_restore returned non-zero (常见的 grant 错误可忽略)"

echo
echo "=== 5) 抽检 ==="
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "
SELECT 'tables=' || COUNT(*) FROM pg_tables WHERE schemaname='public';
SELECT 'users=' || COUNT(*) FROM users;
SELECT 'pilot_users=' || COUNT(*) FROM users WHERE staff_id LIKE 'pilot:%';
SELECT 'colleges=' || COUNT(*) FROM colleges;
SELECT 'kb_entries=' || COUNT(*) FROM kb_entries;
SELECT 'feedbacks=' || COUNT(*) FROM feedbacks;
SELECT 'events=' || COUNT(*) FROM events;
SELECT 'alembic_version=' || version_num FROM alembic_version;
"

echo "=== 6) 清 dump 文件 ==="
docker exec yx_postgres rm -f /tmp/yxg_v2.dump
rm -f /tmp/yxg_v2.dump

echo "[OK] 阶段 C2 完成"
