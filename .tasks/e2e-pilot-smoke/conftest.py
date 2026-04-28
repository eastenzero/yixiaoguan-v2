from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

STUDENT_BASE = "http://192.168.100.165/"
TEACHER_BASE = "http://192.168.100.165:81/"

TASK_DIR = Path(__file__).parent
STATE_PATH = TASK_DIR / "state.json"
SUMMARY_PATH = TASK_DIR / "SUMMARY.md"

RESULTS: dict[str, dict[str, str]] = {}


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke_meta(idx, name): pilot smoke summary metadata")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 390, "height": 844},
        "ignore_https_errors": True,
        "locale": "zh-CN",
    }


@pytest.fixture(scope="session", autouse=True)
def ensure_task_dir():
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        STATE_PATH.write_text("{}", encoding="utf-8")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(update: dict) -> dict:
    state = load_state()
    state.update(update)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return state


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    marker = item.get_closest_marker("smoke_meta")
    if not marker:
        return
    idx = str(marker.kwargs["idx"])
    RESULTS[idx] = {
        "name": marker.kwargs["name"],
        "result": "SKIP" if report.skipped else "PASS" if report.passed else "FAIL",
        "notes": getattr(item, "_smoke_notes", ""),
    }


def pytest_sessionfinish(session, exitstatus):
    state = load_state()

    def row(idx: str, name: str) -> str:
        result = RESULTS.get(idx, {}).get("result", "NOT RUN")
        notes = RESULTS.get(idx, {}).get("notes", "")
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "NOT RUN": "❌"}.get(result, result)
        return f"| {idx} | {name} | {icon} | {notes} |"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    question_id = state.get("question_id") or state.get("conversation_id") or ""
    ai_keywords = state.get("ai_keywords")
    cleanup_note = state.get("cleanup_note", "")
    lines = [
        f"# Pilot Smoke E2E Report — {timestamp}",
        "",
        "| # | Test | Result | Notes |",
        "|---|---|---|---|",
        row("1", "学生登录成功"),
        row("2", "学生 AI 对话有效回复"),
        row("3", "学生提交问题给辅导员"),
        row("4", "辅导员看到该问题"),
        row("5", "Cleanup"),
        "",
        "## 关键截图",
        "- student-home.png",
        "- student-ai-reply.png",
        "- student-question-pending.png",
        "- teacher-question-list.png",
        "",
        "## 运行信息",
        f"- question_id={question_id}",
        f"- 含班级/学院关键词：{'是' if ai_keywords else '否' if ai_keywords is not None else '未知'}",
        f"- cleanup: {cleanup_note or '未记录'}",
        "",
        "## 结论",
        "- 全 PASS → 可启动内测",
        "- 任意 FAIL → 见 trace zip：.tasks/e2e-pilot-smoke/trace-*.zip",
        "",
    ]
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
