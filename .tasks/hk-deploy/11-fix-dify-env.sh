#!/bin/bash
set -e
ENV=/opt/yxg-v2/repo/services/gateway/.env

echo "=== before ==="
grep -E '^DIFY_|^JWT_|^DATABASE_URL' "$ENV" | head -20

# Fix dify_api_url to use host-exposed dify-nginx port 8088
sed -i 's|^DIFY_API_URL=.*|DIFY_API_URL=http://127.0.0.1:8088/v1|' "$ENV"
# Remove any redundant keys we added earlier
sed -i '/^DIFY_BASE_URL=/d' "$ENV"
sed -i '/^DIFY_APP_ID=/d' "$ENV"

echo
echo "=== after ==="
grep -E '^DIFY_' "$ENV"

echo
echo "=== restart ==="
systemctl restart yxg-gateway

echo
echo "=== wait 10s + status ==="
sleep 10
systemctl is-active yxg-gateway || true

echo
echo "=== ss listen 8100? ==="
ss -tlnp | grep ':8100' || echo '(no listener)'

echo
echo "=== last 40 journalctl ==="
journalctl -u yxg-gateway -n 40 --no-pager | tail -40

echo
echo "=== cat last error from stderr if any ==="
journalctl -u yxg-gateway -n 200 --no-pager | grep -iE 'error|traceback|exception|fail' | tail -20 || true
