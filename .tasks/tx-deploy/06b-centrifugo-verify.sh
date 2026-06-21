#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 F2 · Centrifugo ↔ gateway 联通验证
set -e

GW=/home/easten/dev/yixiaoguan-v2/services/gateway
AUTH=$(grep '^centrifugo_proxy_secret=' $GW/.env | cut -d= -f2)
echo "PROXY_SECRET length=${#AUTH}"

echo
echo "=== 1) centrifugo container can reach gateway? ==="
docker exec yxg-centrifugo wget -qO- --timeout=3 http://host.docker.internal:8100/health 2>&1 | head -5 || echo "[!] centrifugo cannot reach gateway via host.docker.internal"

echo
echo "=== 2) /api/internal/centrifugo/subscribe (no auth, expect 401) ==="
curl -s -m 5 -o /dev/null -w 'HTTP %{http_code}\n' \
  -X POST -H 'Content-Type: application/json' \
  -d '{"channel":"conv:1","user":"1"}' \
  http://127.0.0.1:8100/api/internal/centrifugo/subscribe

echo
echo "=== 3) /api/internal/centrifugo/subscribe (with auth, fake conv) ==="
curl -s -m 5 \
  -X POST -H "X-Auth: $AUTH" -H 'Content-Type: application/json' \
  -d '{"channel":"conv:999999","user":"1"}' \
  http://127.0.0.1:8100/api/internal/centrifugo/subscribe
echo
