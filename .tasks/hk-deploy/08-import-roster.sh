#!/usr/bin/env bash
# Step E: import 48 students + 1 teacher (anjing) into 公共事业管理2025-1班 / college 17
# Reads /tmp/students-roster.json (already uploaded)
set -euo pipefail

cd /opt/yxg-v2/repo/services/gateway
. /opt/yxg-v2/venv/bin/activate
set -a
. /opt/yxg-v2/repo/services/gateway/.env
set +a

# 兼容大写小写 env var
DB_URL="${DATABASE_URL:-${database_url:-}}"
[[ -n "$DB_URL" ]] || { echo "[!] DATABASE_URL not set"; exit 1; }
export database_url="$DB_URL"

[[ -f /tmp/students-roster.json ]] || { echo "[!] missing /tmp/students-roster.json"; exit 1; }

python3 <<'PY'
import os, asyncio, json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

COLLEGE_ID = 17
CLASS_NAME = "公共事业管理2025-1班"
GRADE_YEAR = 2025
TEACHER = {
    "staff_id": "anjing",
    "name": "安静",
    "password": "Anjing@yxg2026",
    "role": "teacher",
}
TYPO_FIX = {"4125750036": "4125150036"}

with open("/tmp/students-roster.json", encoding="utf8") as f:
    roster = json.load(f)
for r in roster:
    if r["staff_id"] in TYPO_FIX:
        old, new = r["staff_id"], TYPO_FIX[r["staff_id"]]
        print(f"[typo-fix] {r['name']}: {old} -> {new}")
        r["staff_id"] = new
print(f"Loaded {len(roster)} students")

async def main():
    eng = create_async_engine(os.environ["database_url"])
    async with eng.begin() as c:
        # 1. ensure class
        r = await c.execute(text(
            "select id from classes where name=:n and college_id=:c"
        ), {"n": CLASS_NAME, "c": COLLEGE_ID})
        row = r.first()
        if row:
            class_id = row[0]
            print(f"[class] reuse id={class_id} {CLASS_NAME}")
        else:
            r = await c.execute(text(
                "insert into classes (name, college_id, grade_year) values (:n, :c, :g) returning id"
            ), {"n": CLASS_NAME, "c": COLLEGE_ID, "g": GRADE_YEAR})
            class_id = r.scalar()
            print(f"[class] created id={class_id} {CLASS_NAME}")

        # 2. ensure teacher
        r = await c.execute(text("select id from users where staff_id=:s"), {"s": TEACHER["staff_id"]})
        row = r.first()
        if row:
            print(f"[teacher] {TEACHER['staff_id']} exists id={row[0]} (updating class)")
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

        # 3. import students
        created, updated = 0, 0
        for s in roster:
            sid, name = s["staff_id"], s["name"]
            r = await c.execute(text("select id from users where staff_id=:s"), {"s": sid})
            row = r.first()
            if row:
                await c.execute(text(
                    "update users set college_id=:c, class_id=:cl, name=:n where id=:id"
                ), {"c": COLLEGE_ID, "cl": class_id, "n": name, "id": row[0]})
                updated += 1
                continue
            h = pwd.hash(sid)  # initial password = staff_id
            await c.execute(text(
                "insert into users (staff_id, name, role, college_id, class_id, password_hash, is_active) "
                "values (:s, :n, 'student', :c, :cl, :h, true)"
            ), {"s": sid, "n": name, "c": COLLEGE_ID, "cl": class_id, "h": h})
            created += 1

        print(f"[students] created={created} updated={updated} roster={len(roster)}")

    async with eng.connect() as c:
        r = await c.execute(text("select count(*) from users where role='student'"))
        total = r.scalar()
        r = await c.execute(text("select count(*) from users where class_id=:cl and role='student'"), {"cl": class_id})
        in_class = r.scalar()
        r = await c.execute(text("select staff_id, name from users where class_id=:cl and role='teacher'"), {"cl": class_id})
        teachers = r.fetchall()
        print(f"\n=== VERIFY ===")
        print(f"total students DB: {total}")
        print(f"students in class {CLASS_NAME}: {in_class} (expected 48)")
        print(f"teachers in class:")
        for t in teachers:
            print(f"  {t[0]} | {t[1]}")

asyncio.run(main())
PY

echo ""
echo "[OK] Step E roster imported"
echo "Teacher login: anjing / Anjing@yxg2026"
echo "Student initial password = staff_id (e.g. 4124150001)"

# 删除 PII 文件
rm -f /tmp/students-roster.json
echo "[*] /tmp/students-roster.json deleted (PII)"
