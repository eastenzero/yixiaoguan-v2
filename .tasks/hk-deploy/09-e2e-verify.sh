#!/usr/bin/env bash
# Step F: e2e curl verify (no Dify needed)
set -euo pipefail
BASE=http://127.0.0.1:8080

echo "=== 1. 静态首页 ==="
curl -sS -o /dev/null -w "  http_code=%{http_code} size=%{size_download}\n" $BASE/

echo "=== 2. 学生端 index.html 包含医小管 标识 ==="
curl -sS $BASE/ | grep -oE "<title>[^<]+</title>" || echo "  (no title found)"

echo ""
echo "=== 3. 教师端 (port 8081) ==="
curl -sS http://127.0.0.1:8081/ | grep -oE "<title>[^<]+</title>" || echo "  (no title found)"

echo ""
echo "=== 4. 教师登录 anjing ==="
TR=$(curl -sS -X POST $BASE/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"staff_id":"anjing","password":"Anjing@yxg2026"}' \
    -w "\nHTTP_CODE=%{http_code}")
echo "$TR" | head -10
TEACHER_TOKEN=$(echo "$TR" | python3 -c "import sys,json; d=json.loads(sys.stdin.read().split('HTTP_CODE')[0]); print(d.get('access_token','')[:60])" 2>/dev/null || echo "")
[[ -n "$TEACHER_TOKEN" ]] && echo "  ✓ teacher token: ${TEACHER_TOKEN:0:30}..." || echo "  ✗ no token"

echo ""
echo "=== 5. 学生登录 4124150001 (余文惠) ==="
SR=$(curl -sS -X POST $BASE/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"staff_id":"4124150001","password":"4124150001"}' \
    -w "\nHTTP_CODE=%{http_code}")
echo "$SR" | head -10
STUDENT_TOKEN=$(echo "$SR" | python3 -c "import sys,json; d=json.loads(sys.stdin.read().split('HTTP_CODE')[0]); print(d.get('access_token','')[:60])" 2>/dev/null || echo "")
[[ -n "$STUDENT_TOKEN" ]] && echo "  ✓ student token: ${STUDENT_TOKEN:0:30}..." || echo "  ✗ no token"

echo ""
echo "=== 6. 学生 /api/auth/me with token ==="
if [[ -n "$STUDENT_TOKEN" ]]; then
    FULL_TOKEN=$(echo "$SR" | python3 -c "import sys,json; print(json.loads(sys.stdin.read().split('HTTP_CODE')[0])['access_token'])")
    curl -sS $BASE/api/auth/me -H "Authorization: Bearer $FULL_TOKEN" -w "\n  http=%{http_code}\n"
fi

echo ""
echo "=== 7. announcements list (need auth) ==="
if [[ -n "$STUDENT_TOKEN" ]]; then
    curl -sS $BASE/api/v1/announcements -H "Authorization: Bearer $FULL_TOKEN" -o /dev/null -w "  http=%{http_code}\n"
fi

echo ""
echo "=== 8. gateway log 最新 5 行 ==="
tail -5 /opt/yxg-v2/logs/yxg-gateway.err.log

echo ""
echo "[OK] Step F verification done"
