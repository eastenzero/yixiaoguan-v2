#!/usr/bin/env python3
"""种子数据：插入测试用学院、班级、用户"""
import asyncio
import sys
import os

# 将 gateway 加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'gateway'))

from passlib.hash import bcrypt
from app.database import async_session
from app.models.user import College, Class, User, UserRole

async def seed():
    async with async_session() as session:
        # 学院
        colleges = [
            College(id=1, name="临床医学院"),
            College(id=2, name="护理学院"),
            College(id=3, name="药学院"),
            College(id=4, name="公共卫生学院"),
        ]

        # 班级
        classes = [
            Class(id=1, name="临床2024-1班", college_id=1, grade_year=2024),
            Class(id=2, name="护理2024-1班", college_id=2, grade_year=2024),
        ]

        # 测试用户
        users = [
            User(staff_id="2024010001", name="张小洋",
                 role=UserRole.student, college_id=1, class_id=1,
                 password_hash=bcrypt.hash("2024010001")),
            User(staff_id="2024020001", name="李小辉",
                 role=UserRole.student, college_id=2, class_id=2,
                 password_hash=bcrypt.hash("2024020001")),
            User(staff_id="T001", name="梁淑芬",
                 role=UserRole.teacher, college_id=1,
                 password_hash=bcrypt.hash("liangshufeng")),
            User(staff_id="A001", name="管理员",
                 role=UserRole.admin,
                 password_hash=bcrypt.hash("admin123")),
        ]

        session.add_all(colleges)
        await session.flush()
        session.add_all(classes)
        await session.flush()
        session.add_all(users)
        await session.commit()
        print("Seed data inserted successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
