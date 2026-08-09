#!/usr/bin/env bash
set -Eeuo pipefail

BACKUP_DIR="${1:?usage: restore_drill_remote.sh BACKUP_DIR}"
STAMP="$(date +%Y%m%d%H%M%S)"
PG_NAME="kbfix-pg-restore-${STAMP}"
WEAVIATE_NAME="kbfix-weaviate-restore-${STAMP}"
TMP_ROOT="$(mktemp -d /home/easten/kbfix-restore.XXXXXX)"
RESULT="${BACKUP_DIR}/metadata/restore-drill.txt"

cleanup() {
  docker rm -f "${PG_NAME}" "${WEAVIATE_NAME}" >/dev/null 2>&1 || true
  rm -rf -- "${TMP_ROOT}"
}
trap cleanup EXIT

cd "${BACKUP_DIR}"
sha256sum --check SHA256SUMS >/dev/null

# Use the newer of the two production PostgreSQL client versions so both
# custom-format archives are readable (Dify is PG15, business DB is PG16).
pg_image="$(docker inspect yx_postgres --format '{{.Config.Image}}')"
docker run --rm -d --name "${PG_NAME}" \
  -e POSTGRES_PASSWORD=kbfix_restore_only "${pg_image}" >/dev/null
for _ in $(seq 1 60); do
  docker exec "${PG_NAME}" pg_isready -U postgres >/dev/null 2>&1 && break
  sleep 1
done
docker exec "${PG_NAME}" pg_isready -U postgres >/dev/null
docker cp postgres/dify.dump "${PG_NAME}:/tmp/dify.dump"
docker cp postgres/yixiaoguan_v2.dump "${PG_NAME}:/tmp/yixiaoguan_v2.dump"
docker exec "${PG_NAME}" createdb -U postgres dify_restore
docker exec "${PG_NAME}" pg_restore -U postgres -d dify_restore --no-owner /tmp/dify.dump
docker exec "${PG_NAME}" createdb -U postgres yixiaoguan_restore
docker exec "${PG_NAME}" psql -U postgres -d postgres -X -v ON_ERROR_STOP=1 \
  -c "CREATE ROLE ro_bi NOLOGIN" -c "CREATE ROLE yx_admin NOLOGIN"
docker exec "${PG_NAME}" pg_restore -U postgres -d yixiaoguan_restore --no-owner /tmp/yixiaoguan_v2.dump

dify_counts="$(docker exec "${PG_NAME}" psql -U postgres -d dify_restore -X -qAt -F, \
  -c "SELECT (SELECT count(*) FROM datasets),(SELECT count(*) FROM documents),(SELECT count(*) FROM document_segments),(SELECT count(*) FROM workflows)")"
yx_counts="$(docker exec "${PG_NAME}" psql -U postgres -d yixiaoguan_restore -X -qAt -F, \
  -c "SELECT count(*) FROM kb_entries")"

mkdir -p "${TMP_ROOT}/weaviate"
tar --zstd -C "${TMP_ROOT}/weaviate" -xf weaviate/data.tar.zst
weaviate_image="$(docker inspect docker-weaviate-1 --format '{{.Config.Image}}')"
docker run --rm -d --name "${WEAVIATE_NAME}" \
  -p 127.0.0.1::8080 \
  -v "${TMP_ROOT}/weaviate:/var/lib/weaviate" \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e DEFAULT_VECTORIZER_MODULE=none \
  -e ENABLE_MODULES= \
  -e CLUSTER_HOSTNAME=node1 \
  "${weaviate_image}" >/dev/null
weaviate_port="$(docker port "${WEAVIATE_NAME}" 8080/tcp | awk -F: '{print $NF}')"
for _ in $(seq 1 180); do
  curl -fsS "http://127.0.0.1:${weaviate_port}/v1/.well-known/ready" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS "http://127.0.0.1:${weaviate_port}/v1/.well-known/ready" >/dev/null
schema_classes="$(curl -fsS "http://127.0.0.1:${weaviate_port}/v1/schema" \
  | python3 -c 'import json,sys; print(len(json.load(sys.stdin).get("classes", [])))')"
object_count="$(WEAVIATE_URL="http://127.0.0.1:${weaviate_port}" python3 - <<'PY'
import json
import os
import urllib.request

base = os.environ["WEAVIATE_URL"]
with urllib.request.urlopen(base + "/v1/schema") as response:
    classes = [item["class"] for item in json.load(response).get("classes", [])]

total = 0
for class_name in classes:
    body = json.dumps({"query": "{Aggregate{" + class_name + "{meta{count}}}}"}).encode()
    request = urllib.request.Request(
        base + "/v1/graphql",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise SystemExit(payload["errors"])
    rows = payload["data"]["Aggregate"].get(class_name) or []
    total += sum(int(row["meta"]["count"]) for row in rows)
print(total)
PY
)"

{
  printf 'sha256=PASS\n'
  printf 'dify_counts(datasets,documents,segments,workflows)=%s\n' "${dify_counts}"
  printf 'yx_kb_entries=%s\n' "${yx_counts}"
  printf 'weaviate_schema_classes=%s\n' "${schema_classes}"
  printf 'weaviate_objects=%s\n' "${object_count}"
  printf 'result=PASS\n'
} | tee "${RESULT}"
