#!/bin/bash
TOKEN=$(curl -s -X POST 'http://127.0.0.1:8100/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"4125150001","password":"4125150001"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "token: ${TOKEN:0:20}..."

echo ""
echo "=== Direct WS upgrade (gateway:8100) ==="
curl -si "http://127.0.0.1:8100/ws?token=$TOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -5

echo ""
echo "=== Nginx WS upgrade (yxg.130814.xyz) ==="
curl -ski "https://yxg.130814.xyz/ws?token=$TOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -5

echo ""
echo "=== Nginx WS upgrade (teacher.130814.xyz) ==="
TTOKEN=$(curl -s -X POST 'http://127.0.0.1:8100/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"anjing","password":"Anjing@yxg2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

curl -ski "https://teacher.130814.xyz/ws?token=$TTOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -5
