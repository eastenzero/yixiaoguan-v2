#!/bin/bash
export PGPASSWORD="8BhStEZqoXevqTBuTMbZiDZT6DOJYZow"
DIFY_DS="c2363fef-405b-48ab-a0e2-9274a4186cef"

psql -h 127.0.0.1 -U yxg -d yxg_v2 <<SQL
INSERT INTO college_datasets (college_id, dify_dataset_id)
SELECT id, '${DIFY_DS}'
FROM colleges
ON CONFLICT (college_id) DO NOTHING;
SQL

echo ""
echo "=== Verify ==="
psql -h 127.0.0.1 -U yxg -d yxg_v2 <<'SQL'
SELECT cd.id, cd.college_id, c.name, cd.dify_dataset_id
FROM college_datasets cd
JOIN colleges c ON c.id = cd.college_id
ORDER BY cd.college_id;
SQL
