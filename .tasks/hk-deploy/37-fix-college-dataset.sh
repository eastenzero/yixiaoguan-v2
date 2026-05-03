#!/bin/bash
export PGPASSWORD="8BhStEZqoXevqTBuTMbZiDZT6DOJYZow"

echo "=== Teacher info ==="
psql -h 127.0.0.1 -U yxg -d yxg_v2 -t -A <<'SQL'
SELECT id, staff_id, name, role, college_id, class_id FROM users WHERE role='teacher';
SQL

echo ""
echo "=== Colleges ==="
psql -h 127.0.0.1 -U yxg -d yxg_v2 -t -A <<'SQL'
SELECT id, name FROM colleges ORDER BY id;
SQL

echo ""
echo "=== Existing college_datasets ==="
psql -h 127.0.0.1 -U yxg -d yxg_v2 -t -A <<'SQL'
SELECT * FROM college_datasets;
SQL

echo ""
echo "=== Global dataset config ==="
grep -i 'dify.*dataset' /opt/yxg-v2/repo/services/gateway/.env
