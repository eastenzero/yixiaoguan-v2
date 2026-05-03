#!/bin/bash
# E2E test: HTTPS student login -> create conversation -> chat send (SSE stream)
set -e
BASE=https://yxg.130814.xyz
STAFF_ID=4124150001
PASS=4124150001

echo "=== 1. login ==="
LOGIN=$(curl -sk -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"staff_id\":\"$STAFF_ID\",\"password\":\"$PASS\"}")
echo "$LOGIN"
TOKEN=$(echo "$LOGIN" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
if [ -z "$TOKEN" ]; then echo "ERR: no token"; exit 1; fi
echo "TOKEN=${TOKEN:0:40}..."

echo
echo "=== 2. /api/auth/me ==="
curl -sk "$BASE/api/auth/me" -H "Authorization: Bearer $TOKEN" -w '\nhttp=%{http_code}\n'

echo
echo "=== 3. POST /api/conversations ==="
CONV=$(curl -sk -X POST "$BASE/api/conversations" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"title":"e2e-smoke-test"}')
echo "$CONV"
CONV_ID=$(echo "$CONV" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("id",""))')
if [ -z "$CONV_ID" ]; then echo "ERR: no conv_id"; exit 1; fi
echo "CONV_ID=$CONV_ID"

echo
echo "=== 4. POST /api/chat/send (SSE stream, capped at 25s) ==="
curl -sk -N -X POST "$BASE/api/chat/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  --max-time 25 \
  -d "{\"conv_id\":$CONV_ID,\"content\":\"你好，我是新生，想问下校园情况\"}" 2>&1 | head -30

echo
echo "(end of stream)"
echo
echo "=== 5. final conversation state ==="
curl -sk "$BASE/api/conversations/$CONV_ID" -H "Authorization: Bearer $TOKEN" -w '\nhttp=%{http_code}\n'
