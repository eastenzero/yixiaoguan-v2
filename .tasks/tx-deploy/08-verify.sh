#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 H · 端到端验证(9 项)
# 基础语义沿用 .tasks/r11-deploy-smoke-test.sh,端口和主机改成 tx-new 公网

set +e  # 不要碰到第一个失败就退,全部跑完再总结
log()  { echo -e "\e[36m[H]\e[0m $*"; }
ok()   { echo -e "\e[32m[OK]\e[0m $*"; }
fail() { echo -e "\e[31m[FAIL]\e[0m $*"; FAILS=$((FAILS+1)); }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }

GW=http://127.0.0.1:8100
PUB=http://82.156.129.75
AUTH=$(grep '^centrifugo_proxy_secret=' /home/easten/dev/yixiaoguan-v2/services/gateway/.env | cut -d= -f2)
FAILS=0

log "== 1. /health =="
H=$(curl -s -o /tmp/v-health.json -w '%{http_code}' $GW/health)
if [ "$H" = "200" ]; then
  ok "gateway health 200"
  cat /tmp/v-health.json | python3 -m json.tool | head -20
else
  fail "gateway health $H"
fi

log "== 2. /api/colleges (count=21) =="
N=$(curl -s $GW/api/colleges | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
[ "$N" = "21" ] && ok "colleges=$N" || fail "colleges=$N (expected 21)"

log "== 3. internal subscribe without X-Auth (401) =="
H=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
    -d '{"channel":"conv:1","user":"1"}' \
    $GW/api/internal/centrifugo/subscribe)
[ "$H" = "401" ] && ok "subscribe 401 as expected" || fail "subscribe $H (expected 401)"

log "== 4. internal subscribe with X-Auth, fake conv (200 with deny) =="
H=$(curl -s -o /tmp/v-sub.json -w '%{http_code}' \
    -X POST -H "X-Auth: $AUTH" -H 'Content-Type: application/json' \
    -d '{"channel":"conv:999999","user":"1"}' \
    $GW/api/internal/centrifugo/subscribe)
if [ "$H" = "200" ]; then
  cat /tmp/v-sub.json
  ok "subscribe proxy 200 with deny-check logic"
else
  fail "subscribe with auth $H"
fi

log "== 5. /api/auth/pilot-anonymous (200 + token) =="
curl -s -o /tmp/v-pilot.json -w 'http=%{http_code}\n' \
  -X POST -H 'Content-Type: application/json' \
  -d '{"device_id":"verify-test-12345678"}' \
  $GW/api/auth/pilot-anonymous
TOKEN=$(python3 -c "import json; print(json.load(open('/tmp/v-pilot.json')).get('access_token', ''))" 2>/dev/null)
[ -n "$TOKEN" ] && ok "pilot token OK (len=${#TOKEN})" || fail "no pilot token"

log "== 6. /api/auth/me with pilot token =="
if [ -n "$TOKEN" ]; then
  H=$(curl -s -o /tmp/v-me.json -w '%{http_code}' -H "Authorization: Bearer $TOKEN" $GW/api/auth/me)
  if [ "$H" = "200" ]; then
    ME=$(python3 -c "import json,sys; d=json.load(open('/tmp/v-me.json')); print(f'staff_id={d.get(\"staff_id\")} role={d.get(\"role\")}')")
    ok "$ME"
  else
    fail "/api/auth/me $H"
  fi
fi

log "== 7. /api/feedback/general (200) =="
if [ -n "$TOKEN" ]; then
  H=$(curl -s -o /tmp/v-fb.json -w '%{http_code}' \
      -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
      -d '{"content":"verify smoke","contact":"","device_id":"verify-test-12345678"}' \
      $GW/api/feedback/general)
  [ "$H" = "200" ] && ok "feedback 200" || fail "feedback $H"
fi

log "== 8. /api/track (200) =="
if [ -n "$TOKEN" ]; then
  H=$(curl -s -o /tmp/v-trk.json -w '%{http_code}' \
      -X POST -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
      -d '{"events":[{"event":"verify_smoke","props":{"a":1},"client_ts":"2026-05-09T00:00:00Z"}]}' \
      $GW/api/track)
  [ "$H" = "200" ] && ok "track 200" || fail "track $H"
fi

log "== 9. Centrifugo WS endpoint =="
H=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/connection/websocket)
# centrifugo 对非 upgrade 请求返回 400 是正常
[ "$H" = "400" ] || [ "$H" = "426" ] && ok "centrifugo :8000 alive (HTTP $H 是 WS 不匹配预期)" || fail "centrifugo :8000 $H"

log "== 10. nginx 反代(公网 IP 通路) =="
curl -sI -m 5 $PUB/ | head -2
curl -sI -m 5 $PUB/api/colleges | head -2
curl -s -m 5 $PUB/api/colleges | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'colleges via nginx={len(d)}')" || fail "nginx /api/colleges"

log "== 11. DB 抽检 =="
PGPW=$(grep '^database_url=' /home/easten/dev/yixiaoguan-v2/services/gateway/.env | sed 's|.*://[^:]*:\([^@]*\)@.*|\1|')
PGPASSWORD="$PGPW" psql -h 127.0.0.1 -U yxg -d yixiaoguan_v2 -tA -c "
SELECT 'users total=' || COUNT(*) FROM users;
SELECT 'pilot users=' || COUNT(*) FROM users WHERE staff_id LIKE 'pilot:%';
SELECT 'feedbacks (recent 1h)=' || COUNT(*) FROM feedbacks WHERE created_at > now() - interval '1 hour';
SELECT 'events (recent 1h)=' || COUNT(*) FROM events WHERE created_at > now() - interval '1 hour';
" 2>&1 | head -10

log "== 12. Dify 连通(gateway 调用 Dify API) =="
H=$(curl -s -o /tmp/v-health-full.json -w '%{http_code}' $GW/health)
DIFY_STATUS=$(python3 -c "import json; print(json.load(open('/tmp/v-health-full.json'))['checks'].get('dify', ''))" 2>/dev/null)
[ "$DIFY_STATUS" = "ok" ] && ok "dify via gateway: ok" || fail "dify via gateway: $DIFY_STATUS"

echo ""
echo "================================"
if [ $FAILS -eq 0 ]; then
  echo -e "\e[32m✅ 全部 12 项验证通过\e[0m"
else
  echo -e "\e[31m❌ $FAILS 项失败;排查后重跑\e[0m"
fi
echo "================================"
exit $FAILS
