#!/bin/bash
set -e

BACKUP_DIR="/opt/yxg-v2/backups"
mkdir -p "$BACKUP_DIR"

# --- Gateway DB backup script ---
cat > /opt/yxg-v2/backup-db.sh << 'SCRIPT'
#!/bin/bash
set -e
BACKUP_DIR="/opt/yxg-v2/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# 1) Gateway DB (yxg_v2)
PGPASSWORD="8BhStEZqoXevqTBuTMbZiDZT6DOJYZow" pg_dump \
  -h 127.0.0.1 -p 5432 -U yxg -d yxg_v2 \
  --no-owner --no-privileges \
  | gzip > "$BACKUP_DIR/yxg_v2-$TIMESTAMP.sql.gz"

# 2) Dify DB (inside docker)
docker exec docker-db_postgres-1 pg_dump -U postgres dify \
  | gzip > "$BACKUP_DIR/dify-$TIMESTAMP.sql.gz"

# 3) Cleanup: keep last 14 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +14 -delete

# 4) Report
echo "[$(date)] Backup done:"
ls -lh "$BACKUP_DIR"/*-$TIMESTAMP.sql.gz
SCRIPT

chmod +x /opt/yxg-v2/backup-db.sh

# Run once to verify
echo "=== Running backup now ==="
bash /opt/yxg-v2/backup-db.sh

echo ""
echo "=== Backup files ==="
ls -lh "$BACKUP_DIR"/*.sql.gz

# Install cron: daily at 03:00 UTC
CRON_LINE="0 3 * * * /opt/yxg-v2/backup-db.sh >> /opt/yxg-v2/logs/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v backup-db; echo "$CRON_LINE") | crontab -

echo ""
echo "=== Crontab ==="
crontab -l | grep backup

echo ""
echo "=== DONE ==="
