#!/usr/bin/env bash
# Step D: 部署 Dify 1.13.3 docker-compose 到 64
# 复刻 165 配置（保持 11 容器完整，不硬剪），改端口避开主 nginx :80
set -euo pipefail

DIFY_HOME=/opt/dify-deploy
DIFY_VERSION=1.13.3

# 1. clone dify 源（仅 docker 子目录有用）
mkdir -p $DIFY_HOME
if [[ ! -d $DIFY_HOME/source/.git ]]; then
    echo "[*] cloning dify $DIFY_VERSION (shallow)"
    git clone --depth=1 -b $DIFY_VERSION https://github.com/langgenius/dify.git $DIFY_HOME/source
fi
echo "[*] dify source HEAD: $(git -C $DIFY_HOME/source log -1 --oneline)"

# 2. 复制 docker 配置到工作目录
mkdir -p $DIFY_HOME/docker
cp -rn $DIFY_HOME/source/docker/* $DIFY_HOME/docker/ 2>/dev/null || true
cd $DIFY_HOME/docker

# 3. 准备 .env（基于 .env.example，改关键端口 + secret）
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "[*] .env created from example"
fi

# 生成 SECRET_KEY 和 INIT_PASSWORD
SECRET_KEY=$(openssl rand -base64 42)
INIT_PASSWORD=$(openssl rand -base64 18 | tr -d '/+=' | head -c 16)

# 改关键值（避免端口冲突 + 强 secret）
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
sed -i "s|^INIT_PASSWORD=.*|INIT_PASSWORD=${INIT_PASSWORD}|" .env
sed -i "s|^EXPOSE_NGINX_PORT=.*|EXPOSE_NGINX_PORT=8088|" .env
sed -i "s|^EXPOSE_NGINX_SSL_PORT=.*|EXPOSE_NGINX_SSL_PORT=8443|" .env
# 如果上面 sed 没匹配（行不存在），追加
grep -q '^EXPOSE_NGINX_PORT=' .env || echo "EXPOSE_NGINX_PORT=8088" >> .env
grep -q '^EXPOSE_NGINX_SSL_PORT=' .env || echo "EXPOSE_NGINX_SSL_PORT=8443" >> .env

echo "[*] dify .env configured (NGINX 8088 / SSL 8443)"

# 保存到 secrets 文件
cat >> /root/yxg-secrets.txt <<EOF
DIFY_SECRET_KEY=${SECRET_KEY}
DIFY_INIT_PASSWORD=${INIT_PASSWORD}
EOF
chmod 600 /root/yxg-secrets.txt

# 4. 拉镜像（提前拉避免 up 时超时）
echo ""
echo "==== pulling dify images (may take 5-10 min on first run) ===="
docker compose pull 2>&1 | tail -10

# 5. 启动
echo ""
echo "==== starting dify ===="
docker compose up -d
sleep 8

# 6. 状态
echo ""
echo "==== docker ps ===="
docker compose ps

echo ""
echo "==== nginx port 8088 listening ===="
ss -tlnp | grep :8088 || echo "[!] :8088 not listening, dify-nginx may not be ready"

echo ""
echo "[OK] Step D started. Wait 30-60s for dify-api to become healthy, then run:"
echo "    docker compose ps"
echo "    curl http://127.0.0.1:8088/install"
echo ""
echo "INIT_PASSWORD = ${INIT_PASSWORD}  (saved to /root/yxg-secrets.txt)"
