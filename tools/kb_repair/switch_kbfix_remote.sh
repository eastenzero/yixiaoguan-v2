#!/usr/bin/env bash
set -Eeuo pipefail

EXPECTED_CONFIRM="SWITCH_KBFIX_20260809"
if [[ "${1:-}" != "--confirm" || "${2:-}" != "${EXPECTED_CONFIRM}" ]]; then
  echo "Prepared only; no change made. To switch: $0 --confirm ${EXPECTED_CONFIRM}" >&2
  exit 2
fi

COMPOSE_DIR="/home/easten/dev/dify-deploy/docker"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yaml"
RUN_DIR="/home/easten/dev/dify-deploy/kbfix-run-20260809"
OVERLAY="${RUN_DIR}/docker-compose.kbfix-active.yaml"
BACKUP_ROOT="/home/easten/backups/yixiaoguan-v2"
INITIAL_BACKUP="${BACKUP_ROOT}/kbfix-20260809-162508"
GATEWAY_ENV="/home/easten/dev/yixiaoguan-v2/services/gateway/.env"
MAPPING="${RUN_DIR}/teacher-id-mapping.json"
NEW_DATASET="a5732fe1-a85c-42a8-962c-2a4d8015b56a"
OLD_DATASET="4db0c819-7847-4a95-bf06-5b73a9d41d70"
KBFIX_IMAGE_ID="sha256:fe3dc3d5e946b42eaa2ab4fbc56ba83ff1b0cee8bd92e49dc4a08e7317c4a141"
ORIGINAL_IMAGE_ID="sha256:d1c73b3be4ba3212d4119c77e15230215e8bcf760ed64f80cfea121c277e1108"
STATE_DIR="${BACKUP_ROOT}/switch-$(date +%Y%m%d-%H%M%S)"
LOCK_FILE="${BACKUP_ROOT}/.kbfix-switch.lock"

mkdir -p "${BACKUP_ROOT}"
exec 9>"${LOCK_FILE}"
flock -n 9 || { echo "another KB switch/rollback is running" >&2; exit 1; }

test -f "${INITIAL_BACKUP}/metadata/restore-drill.txt"
grep -q '^result=PASS$' "${INITIAL_BACKUP}/metadata/restore-drill.txt"
(cd "${INITIAL_BACKUP}" && sha256sum --check SHA256SUMS >/dev/null)
test -f "${OVERLAY}"
test -f "${MAPPING}"
test "$(docker image inspect yixiaoguan/dify-api:1.13.3-kbfix-20260809 --format '{{.Id}}')" = "${KBFIX_IMAGE_ID}"
test "$(docker exec docker-redis-1 redis-cli -n 1 LLEN trigger_refresh_publisher | tr -d '\r')" -le 2
grep -q "^dify_global_dataset_id=${OLD_DATASET}$" "${GATEWAY_ENV}"

mkdir -p "${STATE_DIR}"
chmod 700 "${STATE_DIR}"
cp --preserve=mode,timestamps "${GATEWAY_ENV}" "${STATE_DIR}/gateway.env.before"
cp --preserve=mode,timestamps "${COMPOSE_FILE}" "${STATE_DIR}/docker-compose.yaml.before"
cp --preserve=mode,timestamps "${MAPPING}" "${STATE_DIR}/teacher-id-mapping.json"
docker exec yx_postgres pg_dump -U yxg -d yixiaoguan_v2 -Fc -t kb_entries >"${STATE_DIR}/kb_entries.before.dump"
docker exec docker-db_postgres-1 pg_dump -U postgres -d dify -Fc \
  -t apps -t workflows -t app_dataset_joins -t api_tokens >"${STATE_DIR}/dify-app-workflow.before.dump"
docker exec docker-db_postgres-1 psql -U postgres -d dify -X -qAt \
  -c "SELECT count(*) FROM conversations WHERE app_id='8cfaee92-f95c-4316-80a4-ab5d93614772'" \
  >"${STATE_DIR}/formal-conversation-count.before"

docker cp "${RUN_DIR}/publish_formal_workflow.py" docker-api-1:/tmp/publish_formal_workflow.py
docker exec -e PYTHONPATH=/app/api -w /app/api docker-api-1 \
  python /tmp/publish_formal_workflow.py status >"${STATE_DIR}/formal-status.before.log"
python3 "${RUN_DIR}/apply_teacher_id_mapping_remote.py" status --mapping "${MAPPING}" \
  >"${STATE_DIR}/teacher-status.before.json"
grep -q '"old": 319' "${STATE_DIR}/teacher-status.before.json"

rollback_partial() {
  trap - ERR
  set +e
  rollback_status=0
  cp --preserve=mode,timestamps "${STATE_DIR}/gateway.env.before" "${GATEWAY_ENV}" \
    || rollback_status=1
  grep -q "^dify_global_dataset_id=${OLD_DATASET}$" "${GATEWAY_ENV}" \
    || rollback_status=1
  sudo -n systemctl restart yixiaoguan-gateway.service || rollback_status=1
  python3 "${RUN_DIR}/apply_teacher_id_mapping_remote.py" rollback --mapping "${MAPPING}" \
    --confirm ROLLBACK_TEACHER_IDS_20260809 || rollback_status=1
  docker cp "${RUN_DIR}/publish_formal_workflow.py" docker-api-1:/tmp/publish_formal_workflow.py
  docker exec -e PYTHONPATH=/app/api -w /app/api docker-api-1 \
    python /tmp/publish_formal_workflow.py rollback --confirm ROLLBACK_KBFIX_20260809 \
    || rollback_status=1
  (cd "${COMPOSE_DIR}" && docker compose -f "${COMPOSE_FILE}" up -d api worker worker_beat) \
    || rollback_status=1

  for _ in $(seq 1 90); do
    if [[ "$(docker inspect docker-api-1 --format '{{.State.Health.Status}}' 2>/dev/null)" == "healthy" ]]; then
      break
    fi
    sleep 2
  done
  [[ "$(docker inspect docker-api-1 --format '{{.State.Health.Status}}' 2>/dev/null)" == "healthy" ]] \
    || rollback_status=1
  for service in docker-api-1 docker-worker-1 docker-worker_beat-1; do
    [[ "$(docker inspect "${service}" --format '{{.Image}}' 2>/dev/null)" == "${ORIGINAL_IMAGE_ID}" ]] \
      || rollback_status=1
  done

  gateway_rollback_ready=0
  for _ in $(seq 1 60); do
    if systemctl is-active --quiet yixiaoguan-gateway.service \
      && curl --fail --silent --show-error http://127.0.0.1:8100/health \
        >"${STATE_DIR}/gateway-health.after-auto-rollback.pending.json" \
      && grep -q '"status":"ok"' "${STATE_DIR}/gateway-health.after-auto-rollback.pending.json"; then
      gateway_rollback_ready=1
      break
    fi
    sleep 2
  done
  [[ "${gateway_rollback_ready}" -eq 1 ]] || rollback_status=1
  if [[ "${gateway_rollback_ready}" -eq 1 ]]; then
    mv "${STATE_DIR}/gateway-health.after-auto-rollback.pending.json" \
      "${STATE_DIR}/gateway-health.after-auto-rollback.json"
  fi

  if [[ "${rollback_status}" -eq 0 ]]; then
    printf 'result=ROLLED_BACK_AFTER_ERROR time=%s\n' "$(date --iso-8601=seconds)" \
      >"${STATE_DIR}/FAILED_ROLLED_BACK"
  else
    printf 'result=ROLLBACK_INCOMPLETE time=%s\n' "$(date --iso-8601=seconds)" \
      >"${STATE_DIR}/FAILED_ROLLBACK_INCOMPLETE"
  fi
  exit 1
}
trap rollback_partial ERR

(cd "${COMPOSE_DIR}" && docker compose -f "${COMPOSE_FILE}" -f "${OVERLAY}" up -d api worker worker_beat)
for _ in $(seq 1 90); do
  if [[ "$(docker inspect docker-api-1 --format '{{.State.Health.Status}}' 2>/dev/null)" == "healthy" ]]; then
    break
  fi
  sleep 2
done
test "$(docker inspect docker-api-1 --format '{{.State.Health.Status}}')" = "healthy"
for service in docker-api-1 docker-worker-1 docker-worker_beat-1; do
  test "$(docker inspect "${service}" --format '{{.Image}}')" = "${KBFIX_IMAGE_ID}"
done

docker cp "${RUN_DIR}/publish_formal_workflow.py" docker-api-1:/tmp/publish_formal_workflow.py
docker exec -e PYTHONPATH=/app/api -w /app/api docker-api-1 \
  python /tmp/publish_formal_workflow.py switch --confirm SWITCH_KBFIX_20260809 \
  >"${STATE_DIR}/formal-switch.json"

python3 "${RUN_DIR}/apply_teacher_id_mapping_remote.py" switch --mapping "${MAPPING}" \
  --confirm SWITCH_TEACHER_IDS_20260809 >"${STATE_DIR}/teacher-switch.json"

sed -i "s/^dify_global_dataset_id=.*/dify_global_dataset_id=${NEW_DATASET}/" "${GATEWAY_ENV}"
grep -q "^dify_global_dataset_id=${NEW_DATASET}$" "${GATEWAY_ENV}"
sudo -n systemctl restart yixiaoguan-gateway.service
gateway_ready=0
for _ in $(seq 1 60); do
  if systemctl is-active --quiet yixiaoguan-gateway.service \
    && curl --fail --silent --show-error http://127.0.0.1:8100/health \
      >"${STATE_DIR}/gateway-health.pending.json" \
    && grep -q '"status":"ok"' "${STATE_DIR}/gateway-health.pending.json"; then
    gateway_ready=1
    break
  fi
  sleep 2
done
test "${gateway_ready}" -eq 1
mv "${STATE_DIR}/gateway-health.pending.json" "${STATE_DIR}/gateway-health.json"

docker exec docker-db_postgres-1 psql -U postgres -d dify -X -qAt \
  -c "SELECT count(*) FROM conversations WHERE app_id='8cfaee92-f95c-4316-80a4-ab5d93614772'" \
  >"${STATE_DIR}/formal-conversation-count.after"
cmp "${STATE_DIR}/formal-conversation-count.before" "${STATE_DIR}/formal-conversation-count.after"

trap - ERR
ln -sfn "${STATE_DIR}" "${BACKUP_ROOT}/latest-kbfix-switch"
printf 'result=PASS time=%s state=%s\n' "$(date --iso-8601=seconds)" "${STATE_DIR}" >"${STATE_DIR}/PASS"
echo "Switch complete. State: ${STATE_DIR}"
