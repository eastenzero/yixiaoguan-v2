#!/bin/bash
echo "=== Login as admin ==="
TOKEN=$(curl -s http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"admin","password":"Admin@yxg2026"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [ -z "$TOKEN" ]; then
  echo "FAIL: login failed"
  exit 1
fi
echo "Login OK"

echo ""
echo "=== GET /api/admin/users?size=3 ==="
curl -s http://127.0.0.1:8100/api/admin/users?size=3 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null | head -25

echo ""
echo "=== GET /api/admin/users?role=teacher ==="
curl -s "http://127.0.0.1:8100/api/admin/users?role=teacher&size=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'total teachers: {d[\"total\"]}')
for u in d['items']:
    print(f'  {u[\"staff_id\"]} | {u[\"name\"]}')
"

echo ""
echo "=== Non-admin user should get 403 ==="
STU_TOKEN=$(curl -s http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"4125150001","password":"4125150001"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8100/api/admin/users \
  -H "Authorization: Bearer $STU_TOKEN")
echo "Student access → $STATUS (expected 403)"

echo ""
echo "=== DONE ==="
