#!/bin/bash
# 只读探查 165 上业务相关状态
set +e

echo '=== Dify compose dir ==='
for d in /opt/dify-deploy/docker ~/dify-deploy/docker ~/dify/docker /opt/dify/docker; do
  [ -d "$d" ] && echo "FOUND: $d" && ls -la "$d" 2>/dev/null | head -10 && break
done
find /opt /home/easten /root -maxdepth 5 -name 'docker-compose.yml' 2>/dev/null | grep -i dify | head -3

echo
echo '=== Dify compose inspect (the one in use) ==='
DIFY_COMPOSE=$(docker inspect docker-api-1 --format '{{ index .Config.Labels "com.docker.compose.project.working_dir" }}' 2>/dev/null)
echo "working_dir: $DIFY_COMPOSE"
ls -la "$DIFY_COMPOSE" 2>/dev/null | head -5

echo
echo '=== yx_postgres: which PG version + yixiaoguan_v2 size ==='
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -c "SELECT version();" 2>&1 | head -3
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -c "SELECT pg_size_pretty(pg_database_size('yixiaoguan_v2'));" 2>&1 | head -5
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -c "\dt" 2>&1 | tail -8

echo
echo '=== yx_postgres users + pilot ==='
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "SELECT COUNT(*) FROM users;" 2>&1
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "SELECT COUNT(*) FROM users WHERE staff_id LIKE 'pilot:%';" 2>&1
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "SELECT COUNT(*) FROM feedbacks;" 2>&1
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "SELECT COUNT(*) FROM events;" 2>&1
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "SELECT COUNT(*) FROM kb_entries;" 2>&1
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -tA -c "SELECT COUNT(*) FROM colleges;" 2>&1

echo
echo '=== alembic current ==='
cd /home/easten/dev/yixiaoguan-v2/services/gateway 2>/dev/null && source venv/bin/activate 2>/dev/null && alembic current 2>&1 | tail -3

echo
echo '=== Dify DB size ==='
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT pg_size_pretty(pg_database_size('dify'));" 2>&1
docker exec docker-db_postgres-1 psql -U postgres -d dify_plugin -tA -c "SELECT pg_size_pretty(pg_database_size('dify_plugin'));" 2>&1
docker exec docker-db_postgres-1 psql -U postgres -tA -c "SELECT datname FROM pg_database WHERE datistemplate = false;" 2>&1

echo
echo '=== Dify datasets count ==='
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT COUNT(*) FROM datasets;" 2>&1
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT COUNT(*) FROM documents;" 2>&1
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT id, name FROM datasets LIMIT 5;" 2>&1

echo
echo '=== Dify docker volumes size ==='
sudo -n du -sh /var/lib/docker/volumes 2>/dev/null | head -5
sudo -n du -sh /opt/dify-deploy/docker/volumes/* 2>/dev/null 2>&1 | head -10

echo
echo '=== /var/www ==='
ls -la /var/www/yixiaoguan/ 2>/dev/null
du -sh /var/www/yixiaoguan/* 2>/dev/null

echo
echo '=== static files info ==='
find /var/www/yixiaoguan -name index.html 2>/dev/null | head -5
