#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 E · Gateway 部署 + systemd
# 前置:阶段 A/B/C/D 已完成(repo 已 clone,yx_postgres/yx_redis/Dify 在跑)

set -euo pipefail

log()  { echo -e "\e[36m[E]\e[0m $*"; }
ok()   { echo -e "\e[32m[OK]\e[0m $*"; }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }
err()  { echo -e "\e[31m[ERR]\e[0m $*"; }

REPO=/home/easten/dev/yixiaoguan-v2
cd "$REPO"

log "== 1. 拉取最新代码(已 clone,保守起见 fetch + checkout) =="
git fetch origin
# 固定到明确版本,避免 origin/master 被意外推坏
TARGET=$(git rev-parse origin/master)
log "checkout origin/master → $TARGET"
git checkout "$TARGET" -- .
git log -1 --oneline

log "== 2. python 3.12 venv =="
cd "$REPO/services/gateway"
if [ ! -d venv ]; then
  python3.12 -m venv venv
fi
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "venv + deps 安装完成"

log "== 3. 生成 services/gateway/.env =="
if [ -f .env ]; then
  warn "services/gateway/.env 已存在,不覆盖(如需重生成,先手工备份再删)"
else
  # 从 deploy/.env 拉密码
  PGPW=$(grep '^YX_POSTGRES_PASSWORD=' ../../deploy/.env | cut -d= -f2)
  RDPW=$(grep '^YX_REDIS_PASSWORD=' ../../deploy/.env | cut -d= -f2)
  JWT_SECRET=$(openssl rand -base64 48 | tr -d '=' | head -c 64)
  PROXY_SEC=$(grep 'X-Auth' ../../deploy/.env | sed 's/.*"X-Auth": "\([^"]*\)".*/\1/')
  CENT_SECRET=$(grep '^CENTRIFUGO_SECRET=' ../../deploy/.env | cut -d= -f2)
  CENT_API=$(grep '^CENTRIFUGO_API_KEY=' ../../deploy/.env | cut -d= -f2)

  # 业务 user 密码——**必须**与 ub 上一致(03b-pg-migrate 时已建好 yxg 用户),
  # 这里要手工填入或从本地 $env:TEMP\tx-pg-migrate\gateway-env-from-ub.txt 读
  # 我们这里使用一个占位,提示手工填
  YXG_PW="__FILL_FROM_UB_DATABASE_URL__"
  DIFY_URL="http://127.0.0.1:5001/v1"
  DIFY_KEY="__FILL_FROM_UB__"
  DIFY_DATASET="__FILL_FROM_UB__"
  DIFY_DATASET_KEY="__FILL_FROM_UB__"

  cat > .env <<EOF
# TX-NEW gateway .env — 生成于 $(date -Iseconds)
# 格式参考 .env.example + 165 实际值

database_url=postgresql+asyncpg://yxg:${YXG_PW}@127.0.0.1:5432/yixiaoguan_v2
redis_url=redis://:${RDPW}@127.0.0.1:6379/1

jwt_secret=${JWT_SECRET}
jwt_algorithm=HS256
jwt_expire_hours=24

dify_api_url=${DIFY_URL}
dify_api_key=${DIFY_KEY}
dify_global_dataset_id=${DIFY_DATASET}
dify_dataset_api_key=${DIFY_DATASET_KEY}

# R11 pilot mode + centrifugo proxy
pilot_mode_enabled=true
centrifugo_api_url=http://127.0.0.1:8000
centrifugo_proxy_secret=${PROXY_SEC}
centrifugo_secret=${CENT_SECRET}
centrifugo_api_key=${CENT_API}
EOF
  chmod 600 .env
  warn "⚠️  services/gateway/.env 已生成,但 YXG_PW / DIFY_KEY / DIFY_DATASET 等占位符需要手工填!"
  warn "    从本地 \$env:TEMP\\tx-pg-migrate\\gateway-env-from-ub.txt 拷贝真实值过来"
  warn "    编辑完再继续"
  echo ""
  echo "  vim $REPO/services/gateway/.env"
  echo ""
  read -p "编辑完了? 按回车继续,Ctrl-C 取消..." _
fi

log "== 4. 验证 .env 没留占位符 =="
if grep -E '__FILL_FROM_UB_' .env; then
  err ".env 还有占位符,先填完再继续"
  exit 1
fi
ok ".env 检查通过"

log "== 5. 验证 DB 连接 =="
source venv/bin/activate
DATABASE_URL=$(grep '^database_url=' .env | cut -d= -f2-)
# 改成 sync driver 用 psql 快速测
PG_CONN=$(echo "$DATABASE_URL" | sed 's|postgresql+asyncpg://|postgresql://|')
PGPASSWORD=$(echo "$PG_CONN" | sed 's|.*://[^:]*:\([^@]*\)@.*|\1|') \
  psql "$PG_CONN" -c "SELECT 'connected' AS status;" 2>&1 | head -5
ok "DB 连接 OK"

log "== 6. alembic upgrade head =="
alembic current 2>&1 | tail -3
alembic upgrade head
alembic current 2>&1 | tail -3
ok "alembic 对齐"

log "== 7. 创建 logs 目录 + systemd unit =="
mkdir -p /home/easten/logs
sudo cp "$REPO/deploy/systemd/yixiaoguan-gateway.service" /etc/systemd/system/
# unit 里 WorkingDirectory 和 EnvironmentFile 已经是 /home/easten/dev/yixiaoguan-v2/services/gateway,完美
sudo systemctl daemon-reload

log "== 8. 启动 =="
sudo systemctl enable --now yixiaoguan-gateway
sleep 3

if systemctl is-active --quiet yixiaoguan-gateway; then
  ok "yixiaoguan-gateway: active"
else
  err "启动失败"
  sudo journalctl -u yixiaoguan-gateway -n 40 --no-pager
  exit 1
fi

log "== 9. Health check =="
sleep 2
curl -s http://127.0.0.1:8100/health | python3 -m json.tool | head -30 || warn "health 调用失败"

ok "阶段 E 完成"
echo ""
echo "下一步: 跑 06-centrifugo.sh"
