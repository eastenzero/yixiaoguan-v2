#!/usr/bin/env bash
set -Eeuo pipefail

COMPOSE_DIR="/home/easten/dev/dify-deploy/docker"
BACKUP_ROOT="/home/easten/backups/yixiaoguan-v2"
STAMP="${1:-$(date +%Y%m%d-%H%M%S)}"
ARCHIVE_DIR="${BACKUP_ROOT}/queue-archive-${STAMP}"
ACTIVE_KEY="trigger_refresh_publisher"
QUARANTINE_KEY="${ACTIVE_KEY}:kbfix-quarantine:${STAMP}"
TEST_REDIS="kbfix-queue-restore-${STAMP}"

cleanup() {
  docker rm -f "${TEST_REDIS}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

mkdir -p "${ARCHIVE_DIR}"
chmod 700 "${ARCHIVE_DIR}"
redis_image="$(docker inspect docker-redis-1 --format '{{.Config.Image}}')"
before_count="$(docker exec docker-redis-1 redis-cli -n 1 LLEN "${ACTIVE_KEY}" | tr -d '\r')"
before_memory="$(docker exec docker-redis-1 redis-cli -n 1 MEMORY USAGE "${ACTIVE_KEY}" | tr -d '\r')"
[[ "${before_count}" =~ ^[0-9]+$ && "${before_count}" -gt 0 ]]

dump_key() {
  local key="$1"
  local destination="$2"
  docker exec docker-api-1 python -c \
    'import os,redis,sys; data=redis.Redis.from_url(os.environ["CELERY_BROKER_URL"]).dump(sys.argv[1]); assert data is not None; sys.stdout.buffer.write(data)' \
    "${key}" >"${destination}"
  [[ -s "${destination}" ]]
}

restore_test() {
  local source="$1"
  local expected="$2"
  local test_key="$3"
  docker exec -i "${TEST_REDIS}" redis-cli -x RESTORE "${test_key}" 0 \
    <"${source}" >/dev/null
  local restored
  restored="$(docker exec "${TEST_REDIS}" redis-cli LLEN "${test_key}" | tr -d '\r')"
  [[ "${restored}" == "${expected}" ]]
}

docker run --rm -d --name "${TEST_REDIS}" "${redis_image}" >/dev/null
for _ in $(seq 1 30); do
  docker exec "${TEST_REDIS}" redis-cli PING >/dev/null 2>&1 && break
  sleep 1
done
docker exec "${TEST_REDIS}" redis-cli PING >/dev/null

# Prove the active payload is RESTORE-compatible before moving the live key.
dump_key "${ACTIVE_KEY}" "${ARCHIVE_DIR}/pre-rename.dump"
restore_test "${ARCHIVE_DIR}/pre-rename.dump" "${before_count}" restored_pre

renamed="$(docker exec docker-redis-1 redis-cli -n 1 RENAMENX "${ACTIVE_KEY}" "${QUARANTINE_KEY}" | tr -d '\r')"
[[ "${renamed}" == "1" ]]

cd "${COMPOSE_DIR}"
docker compose up -d --force-recreate worker
for _ in $(seq 1 90); do
  state="$(docker inspect docker-worker-1 --format '{{.State.Status}}')"
  [[ "${state}" == "running" ]] && break
  sleep 1
done
[[ "${state:-}" == "running" ]]
worker_queues="$(docker inspect docker-worker-1 --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | sed -n 's/^CELERY_WORKER_QUEUES=//p')"
grep -q 'trigger_refresh_publisher' <<<"${worker_queues}"

# Archive the exact quarantined backlog, including messages that arrived while
# the first dump was being produced, and prove it can also be restored.
final_count="$(docker exec docker-redis-1 redis-cli -n 1 LLEN "${QUARANTINE_KEY}" | tr -d '\r')"
dump_key "${QUARANTINE_KEY}" "${ARCHIVE_DIR}/trigger_refresh_publisher.dump"
restore_test "${ARCHIVE_DIR}/trigger_refresh_publisher.dump" "${final_count}" restored_final

unlinked="$(docker exec docker-redis-1 redis-cli -n 1 UNLINK "${QUARANTINE_KEY}" | tr -d '\r')"
[[ "${unlinked}" == "1" ]]
active_after="$(docker exec docker-redis-1 redis-cli -n 1 LLEN "${ACTIVE_KEY}" | tr -d '\r')"
used_memory_after="$(docker exec docker-redis-1 redis-cli INFO memory \
  | tr -d '\r' | sed -n 's/^used_memory://p')"

{
  printf 'active_key=%s\n' "${ACTIVE_KEY}"
  printf 'quarantine_key=%s\n' "${QUARANTINE_KEY}"
  printf 'before_count=%s\n' "${before_count}"
  printf 'final_archived_count=%s\n' "${final_count}"
  printf 'before_key_memory=%s\n' "${before_memory}"
  printf 'active_after=%s\n' "${active_after}"
  printf 'redis_used_memory_after=%s\n' "${used_memory_after}"
  printf 'worker_queue_enabled=true\n'
  printf 'restore_test=PASS\n'
} >"${ARCHIVE_DIR}/metadata.txt"
find "${ARCHIVE_DIR}" -type f ! -name SHA256SUMS -print0 \
  | sort -z | xargs -0 sha256sum >"${ARCHIVE_DIR}/SHA256SUMS"
cd "${ARCHIVE_DIR}"
sha256sum --check SHA256SUMS >/dev/null

printf 'archive=%s before=%s archived=%s active_after=%s result=PASS\n' \
  "${ARCHIVE_DIR}" "${before_count}" "${final_count}" "${active_after}"
