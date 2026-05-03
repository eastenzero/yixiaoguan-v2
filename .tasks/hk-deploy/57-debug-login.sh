#!/bin/bash
source /opt/yxg-v2/venv/bin/activate
cd /opt/yxg-v2/repo/services/gateway
set -a; source .env 2>/dev/null; set +a

python3 << 'PY'
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.hash import bcrypt

async def main():
    eng = create_async_engine(os.environ.get("DATABASE_URL") or os.environ["database_url"])
    async with eng.connect() as c:
        r = await c.execute(text("SELECT id, staff_id, password_hash, is_active FROM users WHERE staff_id='anjing'"))
        row = r.fetchone()
        if not row:
            print("ERROR: user anjing not found!")
            return
        
        uid, sid, ph, active = row
        print(f"id={uid} staff_id={sid} active={active}")
        print(f"password_hash={ph}")
        print()
        
        # Test passwords
        for pwd in ["Anjing@yxg2026", "anjing", "Anjing@yxg2026 "]:
            try:
                ok = bcrypt.verify(pwd, ph)
                print(f"  verify('{pwd}') = {ok}")
            except Exception as e:
                print(f"  verify('{pwd}') ERROR: {e}")
        
        # Now check admin for comparison
        r2 = await c.execute(text("SELECT id, staff_id, password_hash FROM users WHERE staff_id='admin'"))
        row2 = r2.fetchone()
        if row2:
            print(f"\nadmin hash={row2[2]}")
            print(f"  verify('Admin@yxg2026') = {bcrypt.verify('Admin@yxg2026', row2[2])}")

        # Re-hash and compare structure
        print(f"\nHash structure check:")
        print(f"  anjing hash starts with: {ph[:7]}")
        new_hash = bcrypt.using(rounds=12).hash("Anjing@yxg2026")
        print(f"  fresh hash starts with:  {new_hash[:7]}")
        print(f"  anjing hash length: {len(ph)}")
        print(f"  fresh hash length:  {len(new_hash)}")

asyncio.run(main())
PY
