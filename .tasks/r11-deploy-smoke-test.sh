#!/bin/bash
# R11 backend smoke test
# 在 165 上执行：bash /tmp/r11-deploy-smoke-test.sh

set -u

GW=http://localhost:8100
AUTH=$(grep '^centrifugo_proxy_secret=' ~/dev/yixiaoguan-v2/services/gateway/.env | cut -d= -f2)

echo "================================"
echo "R11 backend smoke test"
echo "================================"
echo ""

# 1. health
echo "[1] /health"
curl -s -o /tmp/r11-health.json -w "HTTP %{http_code}\n" $GW/health
cat /tmp/r11-health.json | head -1
echo ""

# 2. colleges (no auth)
echo "[2] /api/colleges (no auth, count expected 21)"
COUNT=$(curl -s $GW/api/colleges | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
echo "count=$COUNT"
echo ""

# 3. internal subscribe (no X-Auth → expect 401)
echo "[3] /api/internal/centrifugo/subscribe without X-Auth (expect 401)"
curl -s -o /tmp/r11-int1.json -w "HTTP %{http_code}\n" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"channel":"conv:1","user":"1"}' \
  $GW/api/internal/centrifugo/subscribe
cat /tmp/r11-int1.json
echo ""

# 4. internal subscribe (with X-Auth, conv that doesn't exist → expect 200 with deny)
echo "[4] /api/internal/centrifugo/subscribe with X-Auth, fake conv (expect 200 with deny)"
curl -s -o /tmp/r11-int2.json -w "HTTP %{http_code}\n" \
  -X POST -H "X-Auth: $AUTH" -H 'Content-Type: application/json' \
  -d '{"channel":"conv:999999","user":"1"}' \
  $GW/api/internal/centrifugo/subscribe
cat /tmp/r11-int2.json
echo ""

# 5. pilot-anonymous (expect 200)
echo "[5] /api/auth/pilot-anonymous (expect 200 + token)"
curl -s -o /tmp/r11-pilot.json -w "HTTP %{http_code}\n" \
  -X POST -H 'Content-Type: application/json' \
  -d '{"device_id":"deploy-test-12345678"}' \
  $GW/api/auth/pilot-anonymous
TOKEN=$(python3 -c "import json; print(json.load(open('/tmp/r11-pilot.json')).get('access_token','NONE'))")
if [ "$TOKEN" = "NONE" ] || [ -z "$TOKEN" ]; then
  echo "FAIL: no access_token"
  cat /tmp/r11-pilot.json
else
  echo "OK: got access_token (len=${#TOKEN})"
fi
echo ""

# 6. /api/auth/me (with token)
echo "[6] /api/auth/me with pilot token (expect staff_id starting with pilot:)"
if [ "$TOKEN" != "NONE" ] && [ -n "$TOKEN" ]; then
  curl -s -o /tmp/r11-me.json -w "HTTP %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    $GW/api/auth/me
  cat /tmp/r11-me.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'staff_id={d.get(\"staff_id\")} role={d.get(\"role\")}')"
fi
echo ""

# 7. /api/feedback/general (with token)
echo "[7] /api/feedback/general (expect 200)"
if [ "$TOKEN" != "NONE" ] && [ -n "$TOKEN" ]; then
  curl -s -o /tmp/r11-fb.json -w "HTTP %{http_code}\n" \
    -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d '{"content":"smoke test feedback","contact":"","device_id":"deploy-test-12345678"}' \
    $GW/api/feedback/general
  cat /tmp/r11-fb.json
fi
echo ""

# 8. /api/track (with token)
echo "[8] /api/track (expect 200)"
if [ "$TOKEN" != "NONE" ] && [ -n "$TOKEN" ]; then
  curl -s -o /tmp/r11-track.json -w "HTTP %{http_code}\n" \
    -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d '{"events":[{"event":"smoke_test","props":{"a":1},"client_ts":"2026-05-08T12:00:00Z"}]}' \
    $GW/api/track
  cat /tmp/r11-track.json
fi
echo ""

# 9. DB check: pilot user + feedback row + event row
echo "[9] DB check"
PGPASSWORD_FROM_ENV=$(grep '^database_url=' ~/dev/yixiaoguan-v2/services/gateway/.env | sed 's|.*://[^:]*:\([^@]*\)@.*|\1|')
DB=yixiaoguan_v2
psql "postgresql://yxg:${PGPASSWORD_FROM_ENV}@localhost:5432/${DB}" -t -A -c "
SELECT 'pilot users' as label, COUNT(*) FROM users WHERE staff_id LIKE 'pilot:%';
SELECT 'feedbacks (last 1min)', COUNT(*) FROM feedbacks WHERE created_at > now() - interval '1 minute';
SELECT 'events (last 1min)', COUNT(*) FROM events WHERE created_at > now() - interval '1 minute';
SELECT 'chat_analytics columns added', column_name FROM information_schema.columns WHERE table_name='chat_analytics' AND column_name IN ('prompt_tokens','total_price','currency','latency_seconds') ORDER BY column_name;
" 2>&1

echo ""
echo "================================"
echo "smoke test done"
echo "================================"
