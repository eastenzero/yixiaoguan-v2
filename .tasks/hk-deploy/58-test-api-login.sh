#!/bin/bash
echo "=== Login anjing with correct password ==="
RESP=$(curl -s -w '\n%{http_code}' http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"anjing","password":"Anjing@yxg2026"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | head -n -1)
echo "HTTP $CODE"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo ""
echo "=== Login admin ==="
RESP2=$(curl -s -w '\n%{http_code}' http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"admin","password":"Admin@yxg2026"}')
CODE2=$(echo "$RESP2" | tail -1)
BODY2=$(echo "$RESP2" | head -n -1)
echo "HTTP $CODE2"
echo "$BODY2" | python3 -m json.tool 2>/dev/null || echo "$BODY2"

echo ""
echo "=== Login student 4125150001 with staff_id as password ==="
RESP3=$(curl -s -w '\n%{http_code}' http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"4125150001","password":"4125150001"}')
CODE3=$(echo "$RESP3" | tail -1)
BODY3=$(echo "$RESP3" | head -n -1)
echo "HTTP $CODE3"
echo "$BODY3" | python3 -m json.tool 2>/dev/null || echo "$BODY3"
