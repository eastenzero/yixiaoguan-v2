#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 C1 · 起 yx_postgres + yx_redis
# 先 clone 仓库拿到 deploy/docker-compose.yxdata.yml,再 compose up

set -euo pipefail

log()  { echo -e "\e[36m[C1]\e[0m $*"; }
ok()   { echo -e "\e[32m[OK]\e[0m $*"; }
warn() { echo -e "\e[33m[WARN]\e[0m $*"; }

REPO=/home/easten/dev/yixiaoguan-v2

log "== 1. 克隆仓库(如不存在) =="
if [ ! -d "$REPO/.git" ]; then
  mkdir -p /home/easten/dev
  cd /home/easten/dev
  git clone https://github.com/eastenzero/yixiaoguan-v2.git
  ok "仓库已克隆"
else
  ok "仓库已存在"
fi

cd "$REPO"
git fetch origin
log "当前 HEAD: $(git rev-parse --short HEAD) ($(git log -1 --format='%s'))"
log "远端 HEAD: $(git rev-parse --short origin/master)"

log "== 2. 检查 / 生成 deploy/.env =="
if [ -f deploy/.env ]; then
  warn "deploy/.env 已存在,跳过生成(保留现有值)"
else
  # 生成 64 位随机密码
  PGPW=$(openssl rand -hex 16)
  RDPW=$(openssl rand -hex 16)
  CENT_SECRET=$(openssl rand -hex 16)
  CENT_API=$(openssl rand -hex 16)
  PROXY_SEC=$(openssl rand -hex 16)
  DIFY_K="placeholder-will-be-filled-in-E-step"
  JWT_K=$(openssl rand -base64 48 | tr -d '=' | head -c 64)

  cat > deploy/.env <<EOF
# TX-NEW 生成 $(date -Iseconds)
DIFY_API_KEY=${DIFY_K}
JWT_SECRET=${JWT_K}

# Centrifugo
CENTRIFUGO_SECRET=${CENT_SECRET}
CENTRIFUGO_API_KEY=${CENT_API}
CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS={"X-Auth": "${PROXY_SEC}"}

# yx_postgres / yx_redis
YX_POSTGRES_USER=yx_admin
YX_POSTGRES_PASSWORD=${PGPW}
YX_POSTGRES_DB=yixiaoguan
YX_REDIS_PASSWORD=${RDPW}
EOF
  chmod 600 deploy/.env
  ok "deploy/.env 已生成 (mode 600)"
fi

log "== 3. 起 yx_postgres + yx_redis =="
cd "$REPO/deploy"
docker compose -f docker-compose.yxdata.yml up -d
sleep 8

log "== 4. 验证 =="
docker ps --filter name=yx_postgres --filter name=yx_redis --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
PGPW=$(grep '^YX_POSTGRES_PASSWORD=' deploy/.env | cut -d= -f2)
RDPW=$(grep '^YX_REDIS_PASSWORD=' deploy/.env | cut -d= -f2)

# PG 健康
docker exec yx_postgres psql -U yx_admin -c '\l' 2>&1 | head -10 \
  && ok "yx_postgres: OK" \
  || { warn "yx_postgres 连接失败; docker logs yx_postgres"; exit 1; }

# Redis 健康
docker exec yx_redis redis-cli -a "$RDPW" --no-auth-warning ping 2>&1 \
  && ok "yx_redis: OK" \
  || { warn "yx_redis 连接失败"; exit 1; }

log "== 5. 从本机访问测试(经 127.0.0.1:5432/6379) =="
pg_isready -h 127.0.0.1 -p 5432 -U yx_admin && ok "pg_isready localhost:5432 OK"
redis-cli -h 127.0.0.1 -p 6379 -a "$RDPW" --no-auth-warning ping | grep -q PONG \
  && ok "redis localhost:6379 OK"

ok "阶段 C1 完成"
echo ""
echo "下一步: 本地跑 03b-pg-migrate.ps1 从 ub dump yixiaoguan_v2 数据"
