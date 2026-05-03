#!/usr/bin/env bash
# Step D-cont: 改 .env 关键值（端口 + secret + init_password）
set -euo pipefail

cd /opt/dify-deploy/docker

SECRET_KEY=$(openssl rand -base64 42)
INIT_PASSWORD=$(openssl rand -base64 18 | tr -d '/+=' | head -c 16)

sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
sed -i "s|^INIT_PASSWORD=.*|INIT_PASSWORD=${INIT_PASSWORD}|" .env
sed -i "s|^EXPOSE_NGINX_PORT=.*|EXPOSE_NGINX_PORT=8088|" .env
sed -i "s|^EXPOSE_NGINX_SSL_PORT=.*|EXPOSE_NGINX_SSL_PORT=8443|" .env

# 也改 SANDBOX_PORT 防冲突
grep -q '^EXPOSE_SANDBOX_PORT=' .env || echo 'EXPOSE_SANDBOX_PORT=18194' >> .env

echo "[*] key changes applied:"
grep -E '^(EXPOSE_NGINX_PORT|EXPOSE_NGINX_SSL_PORT|INIT_PASSWORD|SECRET_KEY|EXPOSE_SANDBOX_PORT)=' .env

# 保存到 secrets 文件
{
    echo ""
    echo "# Dify ($(date -u +%FT%TZ))"
    echo "DIFY_INIT_PASSWORD=${INIT_PASSWORD}"
    echo "DIFY_SECRET_KEY=${SECRET_KEY}"
} >> /root/yxg-secrets.txt
chmod 600 /root/yxg-secrets.txt

echo ""
echo "==== pulling dify images (may take 5-15 min on first run) ===="
docker compose pull 2>&1 | tail -5

echo ""
echo "==== docker compose up -d ===="
docker compose up -d 2>&1 | tail -25
sleep 10

echo ""
echo "==== status ===="
docker compose ps --format 'table {{.Service}}\t{{.Status}}'

echo ""
echo "==== nginx :8088 ===="
ss -tlnp | grep :8088 || echo "[!] :8088 not listening yet (may need more time)"

echo ""
echo "[OK] Step D dispatched. Check 'docker compose ps' in 60s for healthy status."
echo "DIFY_INIT_PASSWORD: ${INIT_PASSWORD}"
