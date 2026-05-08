#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 F · Centrifugo(docker-compose)
# 前置:deploy/.env 已由阶段 C 生成(有 CENTRIFUGO_* + CHANNEL_PROXY_*)

set -euo pipefail

log()  { echo -e "\e[36m[F]\e[0m $*"; }
ok()   { echo -e "\e[32m[OK]\e[0m $*"; }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }

REPO=/home/easten/dev/yixiaoguan-v2

log "== 1. 校验 deploy/.env 里的 CENTRIFUGO_* =="
cd "$REPO/deploy"
for k in CENTRIFUGO_SECRET CENTRIFUGO_API_KEY CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS; do
  grep -q "^${k}=" .env || { echo "缺少 $k"; exit 1; }
done
ok "deploy/.env 字段齐"

log "== 2. 检查 gateway .env 里的 CENTRIFUGO_PROXY_SECRET 与 .env 里的 X-Auth 一致 =="
GW_PROXY=$(grep '^centrifugo_proxy_secret=' ../services/gateway/.env | cut -d= -f2)
HDR_PROXY=$(grep 'X-Auth' .env | sed 's/.*"X-Auth": "\([^"]*\)".*/\1/')
if [ "$GW_PROXY" != "$HDR_PROXY" ]; then
  warn "⚠️ gateway.centrifugo_proxy_secret ($GW_PROXY) != deploy/.env 的 X-Auth ($HDR_PROXY)"
  warn "   这会导致 subscribe proxy 401; 请统一两处"
  exit 1
fi
ok "PROXY_SECRET 一致"

log "== 3. docker compose up =="
docker compose -f docker-compose.centrifugo.yml up -d
sleep 3

log "== 4. 验证 =="
docker ps --filter name=yxg-centrifugo --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker logs --tail 30 yxg-centrifugo
curl -s -o /dev/null -w "centrifugo direct: HTTP %{http_code}\n" \
  http://127.0.0.1:8000/connection/websocket || warn "centrifugo 本机 :8000 无响应"

ok "阶段 F 完成"
echo ""
echo "下一步: sudo bash 07-nginx-ip.sh"
