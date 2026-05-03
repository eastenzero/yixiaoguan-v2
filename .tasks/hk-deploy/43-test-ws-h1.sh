#!/bin/bash
TOKEN=$(curl -s -X POST 'http://127.0.0.1:8100/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"4125150001","password":"4125150001"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "token: ${TOKEN:0:20}..."

echo ""
echo "=== HTTP/1.1 via Nginx (yxg.130814.xyz) ==="
curl -ski --http1.1 "https://yxg.130814.xyz/ws?token=$TOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -8

echo ""
echo "=== HTTP/1.1 via Nginx (teacher.130814.xyz) ==="
TTOKEN=$(curl -s -X POST 'http://127.0.0.1:8100/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"anjing","password":"Anjing@yxg2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

curl -ski --http1.1 "https://teacher.130814.xyz/ws?token=$TTOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -8

echo ""
echo "=== HTTP/2 via Nginx (expected to fail) ==="
curl -ski "https://yxg.130814.xyz/ws?token=$TOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -5
