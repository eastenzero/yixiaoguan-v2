#!/bin/bash
# Inject Dify API key + base URL into gateway .env, restart gateway, verify
set -e
ENV=/opt/yxg-v2/repo/services/gateway/.env
DIFY_KEY="app-0zqUgdeR2dQ1vJkPeoitneQ6"
DIFY_URL="http://127.0.0.1:8088/v1"
APP_ID="7f1ea428-e784-4e22-b3b1-52e1befbe652"

echo "=== current DIFY_* in .env ==="
grep -E '^DIFY_' "$ENV" || echo '(none)'

echo
echo "=== backup ==="
cp "$ENV" "$ENV.bak.$(date +%s)"

upsert() {
  local k="$1" v="$2"
  if grep -q "^${k}=" "$ENV"; then
    sed -i "s|^${k}=.*|${k}=${v}|" "$ENV"
  else
    echo "${k}=${v}" >> "$ENV"
  fi
}

upsert DIFY_API_KEY "$DIFY_KEY"
upsert DIFY_BASE_URL "$DIFY_URL"
upsert DIFY_APP_ID "$APP_ID"

echo
echo "=== after ==="
grep -E '^DIFY_' "$ENV"

echo
echo "=== restart gateway ==="
systemctl restart yxg-gateway
sleep 3
systemctl is-active yxg-gateway

echo
echo "=== gateway last 20 log lines ==="
journalctl -u yxg-gateway -n 20 --no-pager | tail -20

echo
echo "=== curl /healthz ==="
curl -sS http://127.0.0.1:8100/healthz -w '\nhttp=%{http_code}\n' || echo 'no healthz'
echo "=== curl /docs ==="
curl -sS -o /dev/null http://127.0.0.1:8100/docs -w 'http=%{http_code}\n'
