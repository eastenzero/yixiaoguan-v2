#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 D2 · 等 Dify pg 容器 healthy + restore dump + 验证

set -e

echo "=== 1) wait pg healthy ==="
for i in 1 2 3 4 5 6 7 8 9 10; do
  status=$(docker inspect docker-db_postgres-1 --format '{{.State.Health.Status}}' 2>/dev/null || echo 'none')
  echo "[$i/10] pg health=$status"
  [ "$status" = "healthy" ] && break
  sleep 3
done

echo "=== 2) restore ==="
time (zstd -dc /tmp/dify-all.sql.zst | docker exec -i docker-db_postgres-1 psql -U postgres 2>&1 | tail -30)

echo
echo "=== 3) verify databases ==="
docker exec docker-db_postgres-1 psql -U postgres -tA -c "SELECT datname FROM pg_database WHERE datistemplate=false ORDER BY datname;"

echo
echo "=== 4) verify dify data ==="
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "
SELECT 'apps=' || COUNT(*) FROM apps;
SELECT 'datasets=' || COUNT(*) FROM datasets;
SELECT 'documents=' || COUNT(*) FROM documents;
SELECT 'document_segments=' || COUNT(*) FROM document_segments;
SELECT 'tenants=' || COUNT(*) FROM tenants;
"

echo
echo "=== 5) list datasets ==="
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT id, name, provider, 'docs_count=' || doc_form FROM datasets;"

echo
echo "=== 6) restart api/worker (pickup new schema) ==="
cd /home/easten/dev/dify-deploy/docker
docker compose restart api worker worker_beat 2>&1 | tail -10

echo
echo "=== 7) cleanup ==="
rm -f /tmp/dify-all.sql.zst

echo "[OK] 阶段 D 完成"
