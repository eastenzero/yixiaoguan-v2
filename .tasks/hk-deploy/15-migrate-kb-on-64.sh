#!/bin/bash
# Run on HK 64. Assumes /opt/yxg-v2/scripts-kb/entries already populated by tar pipe.
set -e

REPO=/opt/yxg-v2/repo
ENTRIES_DIR=/opt/yxg-v2/scripts-kb/entries  # populated by tar from ub
DATASET_ID="c2363fef-405b-48ab-a0e2-9274a4186cef"
DATASET_KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
API_URL="http://127.0.0.1:8088/v1"
OUT=/opt/yxg-v2/scripts-kb/migrate_result.csv
ENV=$REPO/services/gateway/.env

echo "=== 1. write DIFY_DATASET_API_KEY into gateway .env ==="
if grep -q '^DIFY_DATASET_API_KEY=' "$ENV"; then
  sed -i "s|^DIFY_DATASET_API_KEY=.*|DIFY_DATASET_API_KEY=${DATASET_KEY}|" "$ENV"
else
  echo "DIFY_DATASET_API_KEY=${DATASET_KEY}" >> "$ENV"
fi
grep -E '^DIFY_' "$ENV"

echo
echo "=== 2. drop SUMMARY page from import set ==="
ls "$ENTRIES_DIR" | wc -l
rm -f "$ENTRIES_DIR"/KB-GEN-SUMMARY-*.md
echo "after drop:"
ls "$ENTRIES_DIR"/KB-*.md | wc -l

echo
echo "=== 3. ensure venv + install deps ==="
cd "$REPO"
if [ ! -d /opt/yxg-v2/venv ]; then
  python3 -m venv /opt/yxg-v2/venv
fi
source /opt/yxg-v2/venv/bin/activate
pip install --quiet httpx pyyaml asyncpg sqlalchemy pydantic-settings pydantic 2>&1 | tail -3 || true
python -c "import httpx, yaml; print('httpx', httpx.__version__, 'yaml ok')"

echo
echo "=== 4. dry-run health check ==="
python -c "
import asyncio, httpx
async def main():
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get('http://127.0.0.1:8088/v1/datasets', headers={'Authorization': 'Bearer ${DATASET_KEY}'})
        print('GET /datasets', r.status_code, r.text[:200])
asyncio.run(main())
"

echo
echo "=== 5. run migrate_kb.py (no-db mode first to avoid PG schema risks) ==="
mkdir -p /opt/yxg-v2/scripts-kb
cd "$REPO"
python scripts/migrate_kb.py \
  --entries-dir "$ENTRIES_DIR" \
  --dataset-id "$DATASET_ID" \
  --api-key "$DATASET_KEY" \
  --api-url "$API_URL" \
  --output "$OUT" \
  --no-db \
  2>&1 | tail -100

echo
echo "=== 6. summary ==="
echo "csv: $OUT"
wc -l "$OUT"
echo "ok count: $(grep -c ',ok,' $OUT || true)"
echo "fail count: $(grep -c ',error,' $OUT || true)"
echo "skip count: $(grep -c ',skip,' $OUT || true)"
