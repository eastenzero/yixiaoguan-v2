#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_DIR="/home/easten/dev/dify-deploy/docker"
BACKUP_ROOT="/home/easten/backups/yixiaoguan-v2"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/daily-${STAMP}"
WEAVIATE_BACKUP_ID="daily-${STAMP}"
LOCK_FILE="${BACKUP_ROOT}/.daily-backup.lock"

mkdir -p "${BACKUP_ROOT}"
exec 9>"${LOCK_FILE}"
flock -n 9 || { echo "backup already running"; exit 0; }

mkdir -p "${BACKUP_DIR}"/{postgres,redis,dify-storage,config,metadata}
chmod 700 "${BACKUP_DIR}"
trap 'printf "result=FAILED time=%s\n" "$(date --iso-8601=seconds)" >"${BACKUP_DIR}/FAILED"' ERR

docker exec docker-db_postgres-1 pg_dump -U postgres -Fc -d dify \
  >"${BACKUP_DIR}/postgres/dify.dump"
docker exec docker-db_postgres-1 pg_dumpall -U postgres --globals-only \
  >"${BACKUP_DIR}/postgres/dify-globals.sql"
docker exec yx_postgres pg_dump -U yxg -Fc -d yixiaoguan_v2 \
  >"${BACKUP_DIR}/postgres/yixiaoguan_v2.dump"
docker exec yx_postgres psql -U yxg -d yixiaoguan_v2 -X -qAt \
  -c "SELECT rolname FROM pg_roles WHERE rolname !~ '^pg_' ORDER BY 1" \
  >"${BACKUP_DIR}/postgres/yixiaoguan-role-names.txt"

redis_before="$(docker exec docker-redis-1 redis-cli LASTSAVE | tr -d '\r')"
docker exec docker-redis-1 redis-cli BGSAVE >/dev/null
for _ in $(seq 1 120); do
  persistence="$(docker exec docker-redis-1 redis-cli INFO persistence | tr -d '\r')"
  redis_after="$(docker exec docker-redis-1 redis-cli LASTSAVE | tr -d '\r')"
  if grep -q '^rdb_bgsave_in_progress:0$' <<<"${persistence}" \
    && grep -q '^rdb_last_bgsave_status:ok$' <<<"${persistence}" \
    && [[ "${redis_after}" -ge "${redis_before}" ]]; then
    break
  fi
  sleep 1
done
grep -q '^rdb_bgsave_in_progress:0$' <<<"${persistence}"
grep -q '^rdb_last_bgsave_status:ok$' <<<"${persistence}"
redis_source="$(docker inspect docker-redis-1 --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}')"
cp --preserve=mode,timestamps "${redis_source}/dump.rdb" "${BACKUP_DIR}/redis/dump.rdb"

docker exec -i docker-api-1 python - "${WEAVIATE_BACKUP_ID}" >"${BACKUP_DIR}/metadata/weaviate-backup.json" <<'PY'
import json
import os
import sys
import time

import requests

backup_id = sys.argv[1]
base = os.environ["WEAVIATE_ENDPOINT"].rstrip("/")
headers = {"Authorization": "Bearer " + os.environ["WEAVIATE_API_KEY"]}
response = requests.post(
    base + "/v1/backups/filesystem",
    headers=headers,
    json={"id": backup_id},
    timeout=30,
)
response.raise_for_status()
deadline = time.time() + 600
payload = response.json()
while time.time() < deadline:
    response = requests.get(
        base + "/v1/backups/filesystem/" + backup_id,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") in {"SUCCESS", "FAILED", "CANCELED"}:
        break
    time.sleep(3)
if payload.get("status") != "SUCCESS":
    raise SystemExit("Weaviate backup failed: " + json.dumps(payload))
print(json.dumps({"id": backup_id, "status": payload["status"]}, ensure_ascii=False))
PY

storage_source="$(docker inspect docker-api-1 --format '{{range .Mounts}}{{if eq .Destination "/app/api/storage"}}{{.Source}}{{end}}{{end}}')"
tar --zstd -C "${storage_source}" -cf "${BACKUP_DIR}/dify-storage/storage.tar.zst" .

cd "${COMPOSE_DIR}"
find "${COMPOSE_DIR}" -maxdepth 1 -type f \
  \( -name '*.yaml' -o -name '*.yml' -o -name '.env' -o -name '.env.*' \) \
  -print0 | tar --null -T - --zstd -cf "${BACKUP_DIR}/config/compose-config.tar.zst"
docker compose config --images >"${BACKUP_DIR}/metadata/images.txt"
docker exec docker-redis-1 redis-cli -n 1 LLEN trigger_refresh_publisher \
  >"${BACKUP_DIR}/metadata/trigger-refresh-publisher.count"
docker exec docker-db_postgres-1 psql -U postgres -d dify -X -qAt \
  -c "COPY (SELECT row_to_json(x) FROM (SELECT id, app_id, version, graph, features, environment_variables, conversation_variables, created_at FROM workflows WHERE id = 'f98baa82-d73f-44b0-aec5-de83078e8b37') x) TO STDOUT" \
  >"${BACKUP_DIR}/metadata/production-workflow.json"

find "${BACKUP_DIR}" -type f ! -name SHA256SUMS -print0 \
  | sort -z | xargs -0 sha256sum >"${BACKUP_DIR}/SHA256SUMS"
cd "${BACKUP_DIR}"
sha256sum --check SHA256SUMS >/dev/null
printf 'result=PASS time=%s weaviate_backup_id=%s\n' \
  "$(date --iso-8601=seconds)" "${WEAVIATE_BACKUP_ID}" >PASS
rm -f FAILED

# Retain 14 daily recovery points. The initial kbfix snapshot is not pruned here.
find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d \
  -name 'daily-*' -mtime +13 -exec rm -rf -- {} +
find "${COMPOSE_DIR}/volumes/weaviate-backups" -mindepth 1 -maxdepth 1 -type d \
  -name 'daily-*' -mtime +13 -exec rm -rf -- {} +

printf 'backup=%s result=PASS\n' "${BACKUP_DIR}"
