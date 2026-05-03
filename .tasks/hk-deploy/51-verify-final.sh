#!/bin/bash
source /opt/yxg-v2/repo/services/gateway/.env 2>/dev/null
export $(grep -v '^#' /opt/yxg-v2/repo/services/gateway/.env | xargs) 2>/dev/null

echo "=== Gateway Health ==="
curl -s http://127.0.0.1:8100/health | python3 -m json.tool 2>/dev/null

echo ""
echo "=== WebSocket (new domain) ==="
# Get token
TOKEN=$(curl -s http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"4125150001","password":"4125150001"}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

echo "Student WS via yxg.xiaoguan.site:"
curl -ski --http1.1 "https://yxg.xiaoguan.site/ws?token=$TOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -3

echo ""
echo "Teacher WS via teacher.xiaoguan.site:"
curl -ski --http1.1 "https://teacher.xiaoguan.site/ws?token=$TOKEN" \
  -H 'Upgrade: websocket' \
  -H 'Connection: Upgrade' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  --max-time 3 2>/dev/null | head -3

echo ""
echo "=== HTTPS Cert Check ==="
for d in yxg.xiaoguan.site teacher.xiaoguan.site dify.xiaoguan.site; do
  echo -n "$d: "
  echo | openssl s_client -connect $d:443 -servername $d 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null | tr '\n' ' '
  echo ""
done
