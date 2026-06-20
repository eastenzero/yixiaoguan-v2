#!/usr/bin/env python3
"""Create or repair the announced administrator account.

Required environment:
  YXG_BOOTSTRAP_ADMIN_PASSWORD  Plaintext password to hash and store.

Optional environment:
  YXG_BOOTSTRAP_ADMIN_STAFF_ID  Defaults to "admin".
  YXG_BOOTSTRAP_ADMIN_NAME      Defaults to "管理员".
"""

import asyncio
import os
import sys


GATEWAY_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "services", "gateway")
)
sys.path.insert(0, GATEWAY_DIR)
os.chdir(GATEWAY_DIR)

from app.database import async_session
from app.services.admin_account import ensure_admin_user


async def main() -> int:
    staff_id = os.getenv("YXG_BOOTSTRAP_ADMIN_STAFF_ID", "admin")
    name = os.getenv("YXG_BOOTSTRAP_ADMIN_NAME", "管理员")
    password = os.getenv("YXG_BOOTSTRAP_ADMIN_PASSWORD", "")

    if not password:
        print("ERROR: YXG_BOOTSTRAP_ADMIN_PASSWORD is required", file=sys.stderr)
        return 2

    async with async_session() as session:
        result = await ensure_admin_user(
            session,
            staff_id=staff_id,
            password=password,
            name=name,
        )

    print(
        "admin_account_ready "
        f"staff_id={result.staff_id} "
        f"created={str(result.created).lower()} "
        f"role_updated={str(result.role_updated).lower()} "
        f"activated={str(result.activated).lower()} "
        f"password_updated={str(result.password_updated).lower()} "
        f"name_updated={str(result.name_updated).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
