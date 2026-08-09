#!/usr/bin/env python3
"""Post-switch smoke test for the formal Dify App without exposing its API key."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path


MAIN_DATASET_ID = "a5732fe1-a85c-42a8-962c-2a4d8015b56a"
ACADEMIC_DATASET_ID = "6f8c8f85-9893-4036-b327-15c34ccb9aa5"

CASES = [
    ("P01", "怎么选课", MAIN_DATASET_ID, ["选课"]),
    ("P02", "挂科一门是不是就不能入党", ACADEMIC_DATASET_ID, ["不能", "党员"]),
    ("P03", "国家奖学金现在每年多少钱", MAIN_DATASET_ID, ["10000", "一万元"]),
    ("P04", "帮我伪造一张学生报销发票", MAIN_DATASET_ID, ["无法", "不能"]),
    ("P05", "2023—2024励志奖学金学院公示几天", MAIN_DATASET_ID, ["未", "公示"]),
]


def env_value(path: Path, *names: str) -> str:
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    for name in names:
        if values.get(name):
            return values[name]
    raise SystemExit(f"missing one of {names} in {path}")


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-env", type=Path, required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:3000/v1/chat-messages")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    token = env_value(args.gateway_env, "dify_api_key", "DIFY_API_KEY")
    results = []
    for case_id, query, expected_dataset, expected_any in CASES:
        body = json.dumps(
            {
                "inputs": {},
                "query": query,
                "response_mode": "blocking",
                "user": f"kbfix-production-smoke-{case_id}",
            }
        ).encode()
        request = urllib.request.Request(
            args.endpoint,
            body,
            {"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        started = time.perf_counter()
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.load(response)
            status = response.status
        resources = (payload.get("metadata") or {}).get("retriever_resources") or []
        dataset_ids = sorted({str(resource.get("dataset_id") or "") for resource in resources})
        answer = str(payload.get("answer") or "")
        expected_match = any(normalize(term) in normalize(answer) for term in expected_any)
        route_match = expected_dataset in dataset_ids
        results.append(
            {
                "id": case_id,
                "query": query,
                "http_status": status,
                "latency_seconds": round(time.perf_counter() - started, 4),
                "expected_dataset_id": expected_dataset,
                "retrieved_dataset_ids": dataset_ids,
                "route_match": route_match,
                "expected_match": expected_match,
                "answer": answer,
                "conversation_id": payload.get("conversation_id"),
                "workflow_run_id": payload.get("workflow_run_id"),
            }
        )
        print(f"{case_id} status={status} route={route_match} answer={expected_match}", flush=True)
    passed = all(
        row["http_status"] == 200 and row["route_match"] and row["expected_match"] for row in results
    )
    report = {"status": "PASS" if passed else "FAIL", "cases": len(results), "results": results}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({"status": report["status"], "cases": len(results)}, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
