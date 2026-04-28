#!/bin/bash
# Idempotent roster import: 1 college (existing #17), 1 class, 1 teacher, 48 students.
# Reads /tmp/students-roster.json on the same host.
set -e
cd /home/easten/dev/yixiaoguan-v2/services/gateway
source venv/bin/activate
set -a
source .env
set +a

python3 << 'PY'
import os, asyncio, json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === config ===
COLLEGE_ID = 17               # 医药管理学院 (existing)
CLASS_NAME = "公共事业管理2025-1班"
GRADE_YEAR = 2025
TEACHER = {
    "staff_id": "anjing",
    "name": "安静",
    "password": "Anjing@yxg2026",
    "role": "teacher",
}
TYPO_FIX = {"4125750036": "4125150036"}   # row 37: 叶涛宁

with open("/tmp/students-roster.json", encoding="utf8") as f:
    roster = json.load(f)

# Apply typo fixes
for r in roster:
    if r["staff_id"] in TYPO_FIX:
        old, new = r["staff_id"], TYPO_FIX[r["staff_id"]]
        print(f"[typo-fix] {r['name']}: {old} -> {new}")
        r["staff_id"] = new

print(f"Loaded {len(roster)} students")

async def main():
    eng = create_async_engine(os.environ["database_url"])
    async with eng.begin() as c:
        # === 1. ensure class ===
        r = await c.execute(text(
            "select id from classes where name=:n and college_id=:c"
        ), {"n": CLASS_NAME, "c": COLLEGE_ID})
        row = r.first()
        if row:
            class_id = row[0]
            print(f"[class] reuse existing id={class_id} name={CLASS_NAME}")
        else:
            r = await c.execute(text(
                "insert into classes (name, college_id, grade_year) values (:n, :c, :g) returning id"
            ), {"n": CLASS_NAME, "c": COLLEGE_ID, "g": GRADE_YEAR})
            class_id = r.scalar()
            print(f"[class] created id={class_id} name={CLASS_NAME}")

        # === 2. ensure teacher ===
        r = await c.execute(text("select id from users where staff_id=:s"), {"s": TEACHER["staff_id"]})
        row = r.first()
        if row:
            print(f"[teacher] {TEACHER['staff_id']} already exists id={row[0]} (skip create, update class)")
            await c.execute(text(
                "update users set college_id=:c, class_id=:cl, name=:n where id=:id"
            ), {"c": COLLEGE_ID, "cl": class_id, "n": TEACHER["name"], "id": row[0]})
        else:
            h = pwd.hash(TEACHER["password"])
            r = await c.execute(text(
                "insert into users (staff_id, name, role, college_id, class_id, password_hash, is_active) "
                "values (:s, :n, :r, :c, :cl, :h, true) returning id"
            ), {"s": TEACHER["staff_id"], "n": TEACHER["name"], "r": TEACHER["role"],
                "c": COLLEGE_ID, "cl": class_id, "h": h})
            print(f"[teacher] created id={r.scalar()} staff_id={TEACHER['staff_id']}")

        # === 3. import students ===
        created, skipped, updated = 0, 0, 0
        for s in roster:
            sid, name = s["staff_id"], s["name"]
            r = await c.execute(text("select id from users where staff_id=:s"), {"s": sid})
            row = r.first()
            if row:
                # Already exists -> just ensure class membership correct
                await c.execute(text(
                    "update users set college_id=:c, class_id=:cl, name=:n where id=:id"
                ), {"c": COLLEGE_ID, "cl": class_id, "n": name, "id": row[0]})
                skipped += 1
                continue
            h = pwd.hash(sid)   # initial password = staff_id
            await c.execute(text(
                "insert into users (staff_id, name, role, college_id, class_id, password_hash, is_active) "
                "values (:s, :n, 'student', :c, :cl, :h, true)"
            ), {"s": sid, "n": name, "c": COLLEGE_ID, "cl": class_id, "h": h})
            created += 1

        print(f"[students] created={created} updated/skipped={skipped} total roster={len(roster)}")

    # === 4. verify ===
    async with eng.connect() as c:
        r = await c.execute(text("select count(*) from users where role='student'"))
        total_students = r.scalar()
        r = await c.execute(text(
            "select count(*) from users where class_id=:cl and role='student'"
        ), {"cl": class_id})
        class_students = r.scalar()
        r = await c.execute(text(
            "select staff_id, name from users where class_id=:cl and role='teacher'"
        ), {"cl": class_id})
        teachers = r.fetchall()
        print()
        print(f"=== VERIFY ===")
        print(f"total students in DB: {total_students}")
        print(f"students in class {CLASS_NAME}: {class_students} (expected 48)")
        print(f"teachers in class:")
        for t in teachers:
            print(f"  {t[0]} | {t[1]}")

asyncio.run(main())
PY
