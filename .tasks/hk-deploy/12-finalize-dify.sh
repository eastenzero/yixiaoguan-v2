#!/bin/bash
set -e
ENV=/opt/yxg-v2/repo/services/gateway/.env
DATASET_ID="c2363fef-405b-48ab-a0e2-9274a4186cef"
APP_KEY="app-0zqUgdeR2dQ1vJkPeoitneQ6"

echo "=== 1. write DIFY_GLOBAL_DATASET_ID ==="
sed -i "s|^DIFY_GLOBAL_DATASET_ID=.*|DIFY_GLOBAL_DATASET_ID=${DATASET_ID}|" "$ENV"
grep -E '^DIFY_' "$ENV"

echo
echo "=== 2. restart gateway ==="
systemctl restart yxg-gateway
sleep 5
systemctl is-active yxg-gateway
ss -tlnp | grep ':8100' && echo 'gateway listening on 8100' || echo 'NOT listening'

echo
echo "=== 3. test Dify v1/parameters with app key (chatflow published?) ==="
curl -sS http://127.0.0.1:8088/v1/parameters \
  -H "Authorization: Bearer ${APP_KEY}" \
  -w '\nhttp=%{http_code}\n'

echo
echo "=== 4. test Dify v1/chat-messages quick smoke (might fail if not published) ==="
curl -sS -N -X POST http://127.0.0.1:8088/v1/chat-messages \
  -H "Authorization: Bearer ${APP_KEY}" \
  -H 'Content-Type: application/json' \
  --max-time 20 \
  -d '{"inputs":{"college_name":"测试学院","campus":"主校区","class_name":"测试班"},"query":"你好","response_mode":"streaming","user":"smoke-test","conversation_id":""}' 2>&1 | head -30
echo
echo '(end of stream)'
