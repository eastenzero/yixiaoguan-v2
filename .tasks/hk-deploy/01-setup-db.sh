#!/usr/bin/env bash
# Step A2: postgres / redis 启动 + db / role / pgvector
# Idempotent: drops + recreates yxg / yxg_v2.
set -euo pipefail

systemctl enable --now postgresql redis-server > /dev/null 2>&1
echo "[*] postgres + redis active"

# 生成强 db 密码
PGPASS=$(openssl rand -base64 33 | tr -d '/+=' | head -c 32)
echo "[*] generated db password (32 chars)"

sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DROP DATABASE IF EXISTS yxg_v2;
DROP ROLE IF EXISTS yxg;
CREATE ROLE yxg WITH LOGIN PASSWORD '${PGPASS}';
CREATE DATABASE yxg_v2 OWNER yxg;
SQL

sudo -u postgres psql -d yxg_v2 -v ON_ERROR_STOP=1 <<SQL
CREATE EXTENSION IF NOT EXISTS vector;
GRANT ALL ON SCHEMA public TO yxg;
SQL

echo "[*] db 'yxg_v2' + role 'yxg' created"

# 验证 pgvector
sudo -u postgres psql -d yxg_v2 -c '\dx vector' | grep -i vector || {
    echo "[!] pgvector not loaded"; exit 2;
}
echo "[*] pgvector extension verified"

# 保存密码到 root only 文件
mkdir -p /root
cat > /root/yxg-secrets.txt <<EOF
# yxg-v2 deployment secrets — DO NOT COMMIT
DB_PASSWORD=${PGPASS}
EOF
chmod 600 /root/yxg-secrets.txt

echo "[*] secrets saved to /root/yxg-secrets.txt"
ls -la /root/yxg-secrets.txt
echo "[*] DB_URL = postgresql+asyncpg://yxg:${PGPASS}@127.0.0.1:5432/yxg_v2"
echo "[OK] Step A2 complete"
