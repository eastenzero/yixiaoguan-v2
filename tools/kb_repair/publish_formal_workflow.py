#!/usr/bin/env python3
"""Prepared switch/rollback for the formal Dify app; never runs without confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime
from typing import Any

from app import app as flask_app
from extensions.ext_database import db
from models import App
from models.dataset import AppDatasetJoin
from models.workflow import Workflow


FORMAL_APP_ID = "8cfaee92-f95c-4316-80a4-ab5d93614772"
ORIGINAL_WORKFLOW_ID = "f98baa82-d73f-44b0-aec5-de83078e8b37"
SHADOW_APP_ID = "76f7ba2c-5c61-47cb-a257-5800cf185e21"
SHADOW_WORKFLOW_ID = "882b1331-6721-4dbe-acca-9d630d0cad37"
MAIN_DATASET_ID = "a5732fe1-a85c-42a8-962c-2a4d8015b56a"
ACADEMIC_DATASET_ID = "6f8c8f85-9893-4036-b327-15c34ccb9aa5"
PRODUCTION_VERSION = "kbfix-production-r7-20260809"


def clone_values(model: type, source: Any, overrides: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for column in model.__table__.columns:
        if column.name == "id":
            continue
        values[column.name] = getattr(source, column.name)
    values.update(overrides)
    return values


def state() -> dict[str, Any]:
    formal = db.session.get(App, FORMAL_APP_ID)
    shadow = db.session.get(App, SHADOW_APP_ID)
    original = db.session.get(Workflow, ORIGINAL_WORKFLOW_ID)
    shadow_workflow = db.session.get(Workflow, SHADOW_WORKFLOW_ID)
    production = (
        db.session.query(Workflow)
        .filter_by(app_id=FORMAL_APP_ID, version=PRODUCTION_VERSION)
        .order_by(Workflow.created_at.desc())
        .first()
    )
    if formal is None or shadow is None or original is None or shadow_workflow is None:
        raise SystemExit("required formal/shadow app or workflow is missing")
    return {
        "formal": formal,
        "shadow": shadow,
        "original": original,
        "shadow_workflow": shadow_workflow,
        "production": production,
    }


def public_status(objects: dict[str, Any]) -> dict[str, Any]:
    formal = objects["formal"]
    shadow_workflow = objects["shadow_workflow"]
    production = objects["production"]
    return {
        "formal_app_id": formal.id,
        "formal_workflow_id": formal.workflow_id,
        "original_workflow_id": ORIGINAL_WORKFLOW_ID,
        "prepared_shadow_workflow_id": shadow_workflow.id,
        "prepared_graph_sha256": hashlib.sha256(shadow_workflow.graph.encode()).hexdigest(),
        "production_workflow_id": production.id if production else None,
        "production_version": PRODUCTION_VERSION,
        "main_dataset_id": MAIN_DATASET_ID,
        "academic_dataset_id": ACADEMIC_DATASET_ID,
        "formal_uses_original": formal.workflow_id == ORIGINAL_WORKFLOW_ID,
        "formal_uses_kbfix": bool(production and formal.workflow_id == production.id),
    }


def switch(objects: dict[str, Any]) -> dict[str, Any]:
    formal = objects["formal"]
    original = objects["original"]
    shadow_workflow = objects["shadow_workflow"]
    production = objects["production"]
    allowed = {ORIGINAL_WORKFLOW_ID}
    if production:
        allowed.add(production.id)
    if formal.workflow_id not in allowed:
        raise SystemExit(f"unexpected formal workflow pointer: {formal.workflow_id}")
    if production is None:
        production = Workflow(
            **clone_values(
                Workflow,
                original,
                {
                    "id": str(uuid.uuid4()),
                    "app_id": formal.id,
                    "version": PRODUCTION_VERSION,
                    "graph": shadow_workflow.graph,
                    "marked_name": "KB蓝绿正式候选 R7",
                    "marked_comment": "由已验收 Shadow R7 发布；原工作流保留用于回滚",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            )
        )
        db.session.add(production)
        db.session.flush()
    for dataset_id in [MAIN_DATASET_ID, ACADEMIC_DATASET_ID]:
        exists = db.session.query(AppDatasetJoin).filter_by(app_id=formal.id, dataset_id=dataset_id).first()
        if exists is None:
            db.session.add(AppDatasetJoin(app_id=formal.id, dataset_id=dataset_id))
    formal.workflow_id = production.id
    formal.updated_at = datetime.now()
    db.session.commit()
    objects["production"] = production
    return public_status(objects)


def rollback(objects: dict[str, Any]) -> dict[str, Any]:
    formal = objects["formal"]
    production = objects["production"]
    allowed = {ORIGINAL_WORKFLOW_ID}
    if production:
        allowed.add(production.id)
    if formal.workflow_id not in allowed:
        raise SystemExit(f"unexpected formal workflow pointer: {formal.workflow_id}")
    formal.workflow_id = ORIGINAL_WORKFLOW_ID
    formal.updated_at = datetime.now()
    db.session.commit()
    return public_status(objects)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["status", "switch", "rollback"])
    parser.add_argument("--confirm")
    args = parser.parse_args()
    expected = {
        "switch": "SWITCH_KBFIX_20260809",
        "rollback": "ROLLBACK_KBFIX_20260809",
    }
    if args.mode in expected and args.confirm != expected[args.mode]:
        raise SystemExit(f"refusing {args.mode}: pass --confirm {expected[args.mode]}")
    with flask_app.app_context():
        objects = state()
        if args.mode == "switch":
            result = switch(objects)
        elif args.mode == "rollback":
            result = rollback(objects)
        else:
            result = public_status(objects)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
