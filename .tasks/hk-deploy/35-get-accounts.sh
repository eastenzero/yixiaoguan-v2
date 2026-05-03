#!/bin/bash
PGPASSWORD="8BhStEZqoXevqTBuTMbZiDZT6DOJYZow" psql -h 127.0.0.1 -U yxg -d yxg_v2 -c "
SELECT id, staff_id, name, role FROM users WHERE role != 'student' ORDER BY id;
"
