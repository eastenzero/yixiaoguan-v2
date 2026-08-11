#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_DIR="/home/easten/dev/dify-deploy/docker"
BACKUP_ROOT="/home/easten/backups/yixiaoguan-v2"
STAMP="${1:-$(date +%Y%m%d-%H%M%S)}"
BACKUP_DIR="${BACKUP_ROOT}/kbfix-${STAMP}"
SERVICES=(api worker worker_beat)
STARTED=0

restore_services() {
  if [[ "${STARTED}" -eq 0 ]]; then
    cd "${COMPOSE_DIR}"
    docker compose start weaviate >/dev/null 2>&1 || true
    docker compose start "${SERVICES[@]}" >/dev/null 2>&1 || true
  fi
}
trap restore_services EXIT

mkdir -p "${BACKUP_DIR}"/{postgres,redis,weaviate,dify-storage,config,metadata}
chmod 700 "${BACKUP_DIR}"

cd "${COMPOSE_DIR}"

# Stop all Dify writers before taking the logical and filesystem snapshots.
docker compose stop "${SERVICES[@]}"

docker exec docker-db_postgres-1 pg_dump -U postgres -Fc -d dify \
  >"${BACKUP_DIR}/postgres/dify.dump"
docker exec docker-db_postgres-1 pg_dumpall -U postgres --globals-only \
  >"${BACKUP_DIR}/postgres/dify-globals.sql"
docker exec yx_postgres pg_dump -U yxg -Fc -d yixiaoguan_v2 \
  >"${BACKUP_DIR}/postgres/yixiaoguan_v2.dump"
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -X -qAt \
  -c "SELECT current_user" >"${BACKUP_DIR}/postgres/yixiaoguan-owner.txt"

redis_before="$(docker exec docker-redis-1 redis-cli LASTSAVE | tr -d '\r')"
docker exec docker-redis-1 redis-cli BGSAVE >/dev/null
for _ in $(seq 1 60); do
  redis_after="$(docker exec docker-redis-1 redis-cli LASTSAVE | tr -d '\r')"
  [[ "${redis_after}" != "${redis_before}" ]] && break
  sleep 1
done
[[ "${redis_after:-${redis_before}}" != "${redis_before}" ]]
redis_source="$(docker inspect docker-redis-1 --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}')"
cp --preserve=mode,timestamps "${redis_source}/dump.rdb" "${BACKUP_DIR}/redis/dump.rdb"

docker compose stop weaviate
weaviate_source="$(docker inspect docker-weaviate-1 --format '{{range .Mounts}}{{if eq .Destination "/var/lib/weaviate"}}{{.Source}}{{end}}{{end}}')"
tar --zstd -C "${weaviate_source}" -cf "${BACKUP_DIR}/weaviate/data.tar.zst" .

storage_source="$(docker inspect docker-api-1 --format '{{range .Mounts}}{{if eq .Destination "/app/api/storage"}}{{.Source}}{{end}}{{end}}')"
tar --zstd -C "${storage_source}" -cf "${BACKUP_DIR}/dify-storage/storage.tar.zst" .

# Preserve deployment inputs without recursively archiving their volume data.
find "${COMPOSE_DIR}" -maxdepth 1 -type f \
  \( -name '*.yaml' -o -name '*.yml' -o -name '.env' -o -name '.env.*' \) \
  -print0 | tar --null -T - --zstd -cf "${BACKUP_DIR}/config/compose-config.tar.zst"

docker inspect docker-api-1 docker-worker-1 docker-worker_beat-1 \
  docker-weaviate-1 docker-redis-1 docker-db_postgres-1 \
  >"${BACKUP_DIR}/metadata/container-inspect.json"
docker compose config --images >"${BACKUP_DIR}/metadata/images.txt"
docker image inspect $(docker compose config --images | sort -u) \
  >"${BACKUP_DIR}/metadata/image-inspect.json"
docker exec docker-redis-1 redis-cli -n 1 LLEN trigger_refresh_publisher \
  >"${BACKUP_DIR}/metadata/trigger-refresh-publisher.count"
docker exec docker-redis-1 redis-cli -n 1 MEMORY USAGE trigger_refresh_publisher \
  >"${BACKUP_DIR}/metadata/trigger-refresh-publisher.memory"

docker exec docker-db_postgres-1 psql -U postgres -d dify -X -qAt \
  -c "COPY (SELECT row_to_json(x) FROM (SELECT id, app_id, version, graph, features, environment_variables, conversation_variables, created_at FROM workflows WHERE id = 'f98baa82-d73f-44b0-aec5-de83078e8b37') x) TO STDOUT" \
  >"${BACKUP_DIR}/metadata/production-workflow.json"
docker exec docker-db_postgres-1 psql -U postgres -d dify -X -qAt \
  -c "COPY (SELECT row_to_json(x) FROM (SELECT id, name, embedding_model, embedding_model_provider, retrieval_model, created_at FROM datasets ORDER BY created_at) x) TO STDOUT" \
  >"${BACKUP_DIR}/metadata/datasets.jsonl"

docker compose start weaviate
docker compose start "${SERVICES[@]}"
STARTED=1

for _ in $(seq 1 60); do
  health="$(docker inspect docker-api-1 --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
  [[ "${health}" == "healthy" ]] && break
  sleep 1
done
[[ "${health:-}" == "healthy" ]]
docker exec docker-api-1 curl --fail --silent --show-error --max-time 10 http://localhost:5001/health \
  >"${BACKUP_DIR}/metadata/post-backup-health.json"

find "${BACKUP_DIR}" -type f ! -name SHA256SUMS -print0 \
  | sort -z | xargs -0 sha256sum >"${BACKUP_DIR}/SHA256SUMS"
sha256sum --check "${BACKUP_DIR}/SHA256SUMS" >/dev/null
printf '%s\n' "${BACKUP_DIR}"
