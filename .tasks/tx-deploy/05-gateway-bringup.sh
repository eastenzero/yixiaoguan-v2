#!/bin/bash
# RUN ON: tx-new (as easten)
# 阶段 E · DB sanity + alembic + systemd 启动
set -e

cd /home/easten/dev/yixiaoguan-v2/services/gateway
source venv/bin/activate

# 从 .env 读出 database_url 给 sanity check 用
DB_URL=$(grep '^database_url=' .env | cut -d= -f2- | sed 's|+asyncpg||')
if [ -z "$DB_URL" ]; then
  echo "[ERR] services/gateway/.env 缺 database_url"
  exit 1
fi

echo "=== 1) DB sanity ==="
DB_URL="$DB_URL" python3 - <<'PY'
import asyncio, asyncpg, os
async def main():
    c = await asyncpg.connect(os.environ['DB_URL'])
    n = await c.fetchval('SELECT COUNT(*) FROM colleges')
    print(f'colleges_count={n}')
    v = await c.fetchval('SELECT version_num FROM alembic_version')
    print(f'alembic_pre={v}')
    await c.close()
asyncio.run(main())
PY

echo
echo "=== 2) alembic upgrade head ==="
alembic current 2>&1 | tail -3
alembic upgrade head 2>&1 | tail -8
alembic current 2>&1 | tail -3

echo
echo "=== 3) install systemd unit ==="
sudo cp /home/easten/dev/yixiaoguan-v2/deploy/systemd/yixiaoguan-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yixiaoguan-gateway 2>&1 | tail -3

echo
echo "=== 4) start ==="
sudo systemctl restart yixiaoguan-gateway
sleep 4
systemctl is-active yixiaoguan-gateway

echo
echo "=== 5) journal (last 10) ==="
sudo journalctl -u yixiaoguan-gateway -n 10 --no-pager

echo
echo "=== 6) /health ==="
curl -s -m 5 http://127.0.0.1:8100/health | python3 -m json.tool || echo "[WARN] curl /health failed"
