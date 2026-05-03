#!/usr/bin/env bash
# Step B1+B2: clone yxg-v2 + venv + .env + alembic upgrade + systemd unit
set -euo pipefail

YXG_HOME=/opt/yxg-v2
REPO_URL=https://github.com/eastenzero/yixiaoguan-v2.git
SECRETS_FILE=/root/yxg-secrets.txt

# 读取 db password
[[ -f $SECRETS_FILE ]] || { echo "[!] missing $SECRETS_FILE (run 01-setup-db.sh first)"; exit 1; }
. $SECRETS_FILE

# 1. clone or pull
mkdir -p $YXG_HOME
if [[ -d $YXG_HOME/repo/.git ]]; then
    echo "[*] repo exists, pulling latest"
    git -C $YXG_HOME/repo fetch --depth=1 origin master
    git -C $YXG_HOME/repo reset --hard origin/master
else
    echo "[*] cloning $REPO_URL"
    git clone --depth=1 -b master $REPO_URL $YXG_HOME/repo
fi
echo "[*] HEAD: $(git -C $YXG_HOME/repo log -1 --oneline)"

# 2. venv + install
if [[ ! -d $YXG_HOME/venv ]]; then
    echo "[*] creating venv"
    python3 -m venv $YXG_HOME/venv
fi
. $YXG_HOME/venv/bin/activate
pip install --upgrade pip wheel -q
pip install -q -r $YXG_HOME/repo/services/gateway/requirements.txt
echo "[*] python deps installed: $(pip list 2>/dev/null | wc -l) packages"

# 3. 生成强 JWT secret + 写 .env
JWT_SECRET=$(openssl rand -base64 48 | tr -d '/+=' | head -c 64)
ENV_FILE=$YXG_HOME/repo/services/gateway/.env
cat > $ENV_FILE <<EOF
DATABASE_URL=postgresql+asyncpg://yxg:${DB_PASSWORD}@127.0.0.1:5432/yxg_v2
REDIS_URL=redis://127.0.0.1:6379/1
JWT_SECRET=${JWT_SECRET}
JWT_EXPIRE_HOURS=24
# Dify endpoints — placeholders, 等 docker-compose 起来再改
DIFY_API_URL=http://127.0.0.1:5001/v1
DIFY_API_KEY=app-pending-replace
DIFY_GLOBAL_DATASET_ID=pending-replace
EOF
chmod 600 $ENV_FILE
echo "[*] .env written ($(wc -l < $ENV_FILE) lines)"

# 同步 secrets file
echo "JWT_SECRET=${JWT_SECRET}" >> $SECRETS_FILE

# 4. alembic upgrade head
cd $YXG_HOME/repo/services/gateway
# alembic 用 sync URL（asyncpg → psycopg2）做 migration
export DATABASE_URL_SYNC="postgresql://yxg:${DB_PASSWORD}@127.0.0.1:5432/yxg_v2"
echo "[*] running alembic upgrade head"
alembic upgrade head 2>&1 | tail -10

# 5. 验证表创建
sudo -u postgres psql -d yxg_v2 -c '\dt' | head -30

echo "[OK] Step B1 complete (gateway repo + venv + db schema ready)"
echo ""
echo "Next: write systemd unit + start service (Step B2)"
