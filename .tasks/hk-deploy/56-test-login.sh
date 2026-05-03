#!/bin/bash
echo "=== Test login: anjing ==="
curl -s http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"anjing","password":"anjing"}' | python3 -m json.tool 2>/dev/null || echo "RAW: $(curl -s http://127.0.0.1:8100/api/auth/login -H 'Content-Type: application/json' -d '{"staff_id":"anjing","password":"anjing"}')"

echo ""
echo "=== Test login: admin ==="
curl -s http://127.0.0.1:8100/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"staff_id":"admin","password":"Admin@yxg2026"}' | python3 -m json.tool 2>/dev/null || echo "FAILED"

echo ""
echo "=== Check users in DB ==="
source /opt/yxg-v2/venv/bin/activate
cd /opt/yxg-v2/repo/services/gateway
set -a; source .env 2>/dev/null; set +a
python3 << 'PY'
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    eng = create_async_engine(os.environ.get("DATABASE_URL") or os.environ["database_url"])
    async with eng.connect() as c:
        r = await c.execute(text("SELECT id, staff_id, name, role, is_active, substring(password_hash,1,20) as ph FROM users ORDER BY id LIMIT 10"))
        rows = r.fetchall()
        for row in rows:
            print(f"  id={row[0]} staff_id={row[1]} name={row[2]} role={row[3]} active={row[4]} hash={row[5]}...")

asyncio.run(main())
PY
