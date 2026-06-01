#!/bin/bash
# debug pilot login from frontend
set -u

echo "[1] direct gateway 8100:"
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"device_id":"debug-direct-12345678"}' \
  http://localhost:8100/api/auth/pilot-anonymous \
  -w "\nHTTP %{http_code}\n"
echo ""

echo "[2] via nginx port 80 (same path):"
curl -s -X POST -H 'Content-Type: application/json' \
  -H 'Origin: http://192.168.100.165' \
  -d '{"device_id":"debug-nginx80-12345678"}' \
  http://localhost/api/auth/pilot-anonymous \
  -w "\nHTTP %{http_code}\n"
echo ""

echo "[3] front-end build assets:"
ls /var/www/yixiaoguan/student/assets/index-*.js 2>/dev/null | head -1
echo ""

echo "[4] index.html content:"
cat /var/www/yixiaoguan/student/index.html
echo ""

echo "[5] config.py default for pilot_mode_enabled:"
grep -A 1 'pilot_mode_enabled' ~/dev/yixiaoguan-v2/services/gateway/app/config.py | head -3
echo ""

echo "[6] gateway .env (R11 keys, redacted):"
grep -E '^(pilot_mode|centrifugo)' ~/dev/yixiaoguan-v2/services/gateway/.env | sed 's/=.*/=<REDACTED>/'
echo ""

echo "[7] gateway log last 30 lines (look for pilot related errors):"
tail -50 /home/easten/logs/yxg-gateway.log 2>&1 | grep -i -E 'pilot|auth|error|exception' | tail -15
echo ""

echo "[8] nginx access log last 5 lines for /api/auth:"
sudo -n grep '/api/auth' /var/log/nginx/access.log 2>&1 | tail -5
