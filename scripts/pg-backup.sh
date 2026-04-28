#!/bin/bash
# Daily pg_dump backup of yixiaoguan_v2 DB (running in yx_postgres docker container).
# Keeps 7 daily snapshots in /home/easten/backups/ with rotation.
set -e
BACKUP_DIR=/home/easten/backups
LOG=/home/easten/logs/pg-backup.log
mkdir -p "$BACKUP_DIR" "$(dirname "$LOG")"
TS=$(date +%Y%m%d-%H%M%S)
OUT="$BACKUP_DIR/yxgv2-$TS.sql.gz"

echo "[$(date -Is)] start backup -> $OUT" >> "$LOG"
sudo docker exec yx_postgres pg_dump -U yxg -d yixiaoguan_v2 --no-owner --no-acl 2>>"$LOG" \
  | gzip > "$OUT"

SIZE=$(stat -c%s "$OUT")
echo "[$(date -Is)] done size=$SIZE bytes" >> "$LOG"

# Rotation: keep last 7 daily backups
find "$BACKUP_DIR" -name 'yxgv2-*.sql.gz' -mtime +7 -delete -print >> "$LOG" 2>&1 || true
