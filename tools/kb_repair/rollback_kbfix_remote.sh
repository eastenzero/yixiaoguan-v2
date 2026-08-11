#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_CONFIRM="ROLLBACK_KBFIX_20260809"
if [[ "${1:-}" != "--confirm" || "${2:-}" != "${EXPECTED_CONFIRM}" ]]; then
  echo "Prepared only; no change made. To rollback: $0 --confirm ${EXPECTED_CONFIRM} [state-dir]" >&2
  exit 2
fi

COMPOSE_DIR="/home/easten/dev/dify-deploy/docker"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yaml"
RUN_DIR="/home/easten/dev/dify-deploy/kbfix-run-20260809"
BACKUP_ROOT="/home/easten/backups/yixiaoguan-v2"
STATE_DIR="${3:-${BACKUP_ROOT}/latest-kbfix-switch}"
GATEWAY_ENV="/home/easten/dev/yixiaoguan-v2/services/gateway/.env"
MAPPING="${RUN_DIR}/teacher-id-mapping.json"
OLD_DATASET="4db0c819-7847-4a95-bf06-5b73a9d41d70"
ORIGINAL_IMAGE_ID="sha256:d1c73b3be4ba3212d4119c77e15230215e8bcf760ed64f80cfea121c277e1108"
LOCK_FILE="${BACKUP_ROOT}/.kbfix-switch.lock"

exec 9>"${LOCK_FILE}"
flock -n 9 || { echo "another KB switch/rollback is running" >&2; exit 1; }
test -f "${STATE_DIR}/gateway.env.before"
test -f "${MAPPING}"

docker cp "${RUN_DIR}/publish_formal_workflow.py" docker-api-1:/tmp/publish_formal_workflow.py
docker exec -e PYTHONPATH=/app/api -w /app/api docker-api-1 \
  python /tmp/publish_formal_workflow.py rollback --confirm ROLLBACK_KBFIX_20260809 \
  >"${STATE_DIR}/formal-rollback.json"

cp --preserve=mode,timestamps "${STATE_DIR}/gateway.env.before" "${GATEWAY_ENV}"
grep -q "^dify_global_dataset_id=${OLD_DATASET}$" "${GATEWAY_ENV}"
sudo -n systemctl restart yixiaoguan-gateway.service

python3 "${RUN_DIR}/apply_teacher_id_mapping_remote.py" rollback --mapping "${MAPPING}" \
  --confirm ROLLBACK_TEACHER_IDS_20260809 >"${STATE_DIR}/teacher-rollback.json"

(cd "${COMPOSE_DIR}" && docker compose -f "${COMPOSE_FILE}" up -d api worker worker_beat)
for _ in $(seq 1 90); do
  if [[ "$(docker inspect docker-api-1 --format '{{.State.Health.Status}}' 2>/dev/null)" == "healthy" ]]; then
    break
  fi
  sleep 2
done
test "$(docker inspect docker-api-1 --format '{{.State.Health.Status}}')" = "healthy"
for service in docker-api-1 docker-worker-1 docker-worker_beat-1; do
  test "$(docker inspect "${service}" --format '{{.Image}}')" = "${ORIGINAL_IMAGE_ID}"
done

gateway_ready=0
for _ in $(seq 1 60); do
  if systemctl is-active --quiet yixiaoguan-gateway.service \
    && curl --fail --silent --show-error http://127.0.0.1:8100/health \
      >"${STATE_DIR}/gateway-health.after-rollback.pending.json" \
    && grep -q '"status":"ok"' "${STATE_DIR}/gateway-health.after-rollback.pending.json"; then
    gateway_ready=1
    break
  fi
  sleep 2
done
test "${gateway_ready}" -eq 1
mv "${STATE_DIR}/gateway-health.after-rollback.pending.json" \
  "${STATE_DIR}/gateway-health.after-rollback.json"
printf 'result=PASS time=%s\n' "$(date --iso-8601=seconds)" >"${STATE_DIR}/ROLLBACK_PASS"
echo "Rollback complete. State: ${STATE_DIR}"
