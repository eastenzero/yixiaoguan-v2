#!/usr/bin/env python3
"""Reversibly disable or re-enable the isolated green Shadow App."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from app import app as flask_app
from extensions.ext_database import db
from models import App


SHADOW_APP_ID = "76f7ba2c-5c61-47cb-a257-5800cf185e21"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["status", "disable", "enable"])
    parser.add_argument("--confirm")
    args = parser.parse_args()
    confirmations = {
        "disable": "DISABLE_GREEN_SHADOW_20260809",
        "enable": "ENABLE_GREEN_SHADOW_20260809",
    }
    if args.mode in confirmations and args.confirm != confirmations[args.mode]:
        raise SystemExit(f"refusing {args.mode}: pass --confirm {confirmations[args.mode]}")
    with flask_app.app_context():
        shadow = db.session.get(App, SHADOW_APP_ID)
        if shadow is None:
            raise SystemExit("shadow app missing")
        if args.mode == "disable":
            shadow.enable_api = False
            shadow.enable_site = False
            shadow.updated_at = datetime.now()
            db.session.commit()
        elif args.mode == "enable":
            shadow.enable_api = True
            shadow.enable_site = False
            shadow.updated_at = datetime.now()
            db.session.commit()
        print(
            json.dumps(
                {
                    "shadow_app_id": shadow.id,
                    "workflow_id": shadow.workflow_id,
                    "enable_api": shadow.enable_api,
                    "enable_site": shadow.enable_site,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
