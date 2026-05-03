#!/bin/bash
# Import v2 final-merged 835 docs into existing dataset (additive, on top of v1 432).
set -e

REPO=/opt/yxg-v2/repo
WORK=/opt/yxg-v2/scripts-kb
ENTRIES_DIR=$WORK/v2-entries
DATASET_ID="c2363fef-405b-48ab-a0e2-9274a4186cef"
DATASET_KEY="dataset-Cw9zcTBywGSgBAlivhRrKn6k"
API_URL="http://127.0.0.1:8088/v1"
OUT=$WORK/migrate_result_v2.csv

echo "=== 1. extract v2 flat tarball ==="
rm -rf "$ENTRIES_DIR"
mkdir -p "$ENTRIES_DIR"
tar -xzf "$WORK/v2-flat.tgz" -C "$WORK/"
mv -f "$WORK/src-v2-flat"/*.md "$ENTRIES_DIR/"
rm -rf "$WORK/src-v2-flat"
ls "$ENTRIES_DIR" | wc -l
echo "sample names:"
ls "$ENTRIES_DIR" | head -3

echo
echo "=== 2. run migrate_kb.py (no-db) on v2 entries ==="
source /opt/yxg-v2/venv/bin/activate
cd "$REPO"
python scripts/migrate_kb.py \
  --entries-dir "$ENTRIES_DIR" \
  --dataset-id "$DATASET_ID" \
  --api-key "$DATASET_KEY" \
  --api-url "$API_URL" \
  --output "$OUT" \
  --no-db \
  2>&1 | tail -30

echo
echo "=== 3. summary ==="
echo "csv: $OUT"
wc -l "$OUT"
echo "ok: $(grep -c ',ok,' $OUT 2>/dev/null || echo 0)"
echo "fail: $(grep -c ',error,' $OUT 2>/dev/null || echo 0)"
echo "skip: $(grep -c ',skip,' $OUT 2>/dev/null || echo 0)"
