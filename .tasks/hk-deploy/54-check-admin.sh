#!/bin/bash
cd /opt/yxg-v2/repo/services/gateway
set -a; source .env 2>/dev/null; set +a

python3 << 'PY'
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    eng = create_async_engine(os.environ.get("DATABASE_URL") or os.environ["database_url"])
    async with eng.connect() as c:
        r = await c.execute(text("SELECT id, staff_id, name, role FROM users WHERE role='admin'"))
        rows = r.fetchall()
        if rows:
            for row in rows:
                print(f"  id={row[0]} staff_id={row[1]} name={row[2]} role={row[3]}")
        else:
            print("  No admin users found!")
            print("  Creating default admin...")
            # Create admin user
            from passlib.hash import bcrypt
            h = bcrypt.using(rounds=12).hash("Admin@yxg2026")
            async with eng.begin() as c2:
                await c2.execute(text(
                    "INSERT INTO users (staff_id, name, role, password_hash, is_active, college_id) "
                    "VALUES ('admin', '系统管理员', 'admin', :h, true, 17) "
                    "ON CONFLICT (staff_id) DO NOTHING"
                ), {"h": h})
            print("  Admin user created: staff_id=admin password=Admin@yxg2026")

asyncio.run(main())
PY
