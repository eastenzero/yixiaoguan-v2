from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, TimeoutError as PlaywrightTimeoutError, expect

from conftest import STUDENT_BASE, TEACHER_BASE, TASK_DIR, load_state, save_state

STUDENT_ID = "4125150001"
STUDENT_PASSWORD = "4125150001"
TEACHER_ID = "anjing"
TEACHER_PASSWORD = "Anjing@yxg2026"
STORAGE_STATE = TASK_DIR / "student-storage-state.json"


def _screenshot(page: Page, name: str) -> None:
    page.screenshot(path=str(TASK_DIR / name), full_page=True)


def _click_text(page: Page, text: str, timeout: int = 10_000) -> None:
    target = page.get_by_text(text, exact=True).first
    target.wait_for(state="visible", timeout=timeout)
    target.click()


def _login_student(page: Page) -> None:
    page.goto(STUDENT_BASE, wait_until="domcontentloaded", timeout=15_000)
    expect(page.get_by_text("学号", exact=True)).to_be_visible(timeout=10_000)
    expect(page.get_by_text("密码", exact=True)).to_be_visible(timeout=10_000)
    page.locator("input").nth(0).fill(STUDENT_ID)
    page.locator("input").nth(1).fill(STUDENT_PASSWORD)
    page.locator("uni-button.submit-btn").click()
    page.wait_for_url(re.compile(r".*/pages/home/index|.*/index"), timeout=15_000)
    expect(page.get_by_text("智慧校园助理", exact=True)).to_be_visible(timeout=10_000)


def _login_teacher(page: Page) -> None:
    page.goto(TEACHER_BASE, wait_until="domcontentloaded", timeout=15_000)
    expect(page.get_by_text("教师工作台")).to_be_visible(timeout=10_000)
    page.locator("input").nth(0).fill(TEACHER_ID)
    page.locator("input").nth(1).fill(TEACHER_PASSWORD)
    page.locator("uni-button.login-btn").click()
    page.wait_for_url(re.compile(r".*/pages/(dashboard|questions)/index"), timeout=15_000)


def _open_student_chat(page: Page) -> None:
    if "/pages/chat/index" not in page.url:
        page.goto(STUDENT_BASE + "#/pages/chat/index", wait_until="domcontentloaded", timeout=15_000)
    expect(page.get_by_text("医小管", exact=True)).to_be_visible(timeout=10_000)
    page.locator("input.input").last.wait_for(state="visible", timeout=10_000)


def _send_student_message(page: Page, text: str) -> int | None:
    conv_ids: list[int] = []

    def capture(response):
        if "/api/conversations" in response.url and response.request.method == "POST":
            try:
                data = response.json()
                if isinstance(data, dict) and data.get("id"):
                    conv_ids.append(int(data["id"]))
            except Exception:
                pass

    page.on("response", capture)
    page.locator("input.input").last.fill(text)
    page.locator(".send-btn").last.click()
    expect(page.get_by_text(text, exact=True)).to_be_visible(timeout=15_000)
    try:
        page.wait_for_response(
            lambda r: "/api/conversations" in r.url and r.request.method == "POST",
            timeout=5_000,
        )
    except PlaywrightTimeoutError:
        pass
    page.remove_listener("response", capture)
    return conv_ids[-1] if conv_ids else None


@pytest.mark.smoke_meta(idx=1, name="学生登录成功")
def test_01_student_login_success(browser: Browser, request):
    context = browser.new_context(storage_state=None)
    page = context.new_page()
    _login_student(page)
    context.storage_state(path=str(STORAGE_STATE))
    _screenshot(page, "student-home.png")
    body_text = page.locator("body").inner_text()
    tab_hits = sum(1 for label in ["首页", "智能问答", "事务导办", "我的"] if label in body_text)
    assert tab_hits == 4
    request.node._smoke_notes = "4 个 tabBar 项可见"
    context.close()


@pytest.mark.smoke_meta(idx=2, name="学生 AI 对话有效回复")
def test_02_student_ai_chat_reply(browser: Browser, request):
    assert STORAGE_STATE.exists(), "student storage_state missing; run login test first"
    context = browser.new_context(storage_state=str(STORAGE_STATE))
    page = context.new_page()
    _open_student_chat(page)
    question = "奖学金怎么申请？"
    conv_id = _send_student_message(page, question)
    if conv_id:
        save_state({"ai_conversation_id": conv_id})
    assistant = page.locator(".ai-msg .markdown-body").last
    expect(assistant).to_contain_text(re.compile(r".{50,}", re.S), timeout=90_000)
    answer = assistant.inner_text(timeout=5_000).strip()
    has_keyword = any(word in answer for word in ["医药管理学院", "公共事业管理", "2025-1"])
    save_state({"ai_keywords": has_keyword})
    _screenshot(page, "student-ai-reply.png")
    request.node._smoke_notes = f"回复 {len(answer)} 字；含班级/学院关键词：{'是' if has_keyword else '否'}"
    context.close()


@pytest.mark.smoke_meta(idx=3, name="学生提交问题给辅导员")
def test_03_student_escalates_question(browser: Browser, request):
    assert STORAGE_STATE.exists(), "student storage_state missing; run login test first"
    marker = f"【e2e-smoke-test-{int(time.time())}】请帮我查一下学位证发放时间"
    context = browser.new_context(storage_state=str(STORAGE_STATE))
    page = context.new_page()
    _open_student_chat(page)
    conv_id = _send_student_message(page, marker)
    save_state({"question_marker": marker, "conversation_id": conv_id})

    # Long-press send opens the manual escalation menu in the current student UI.
    page.locator(".send-btn").last.dispatch_event("longpress")
    _click_text(page, "呼叫老师")
    expect(page.get_by_text(re.compile("已通知老师|等待老师接入"))).to_be_visible(timeout=15_000)
    _screenshot(page, "student-question-pending.png")
    save_state({"question_id": conv_id, "question_status": "pending_teacher"})
    request.node._smoke_notes = f"question_id={conv_id}; 状态=pending_teacher"
    context.close()


@pytest.mark.smoke_meta(idx=4, name="辅导员看到该问题")
def test_04_teacher_can_see_student_question(browser: Browser, request):
    state = load_state()
    marker = state.get("question_marker")
    assert marker, "question marker missing; run escalation test first"
    context = browser.new_context(storage_state=None)
    page = context.new_page()
    _login_teacher(page)
    if "/pages/questions/index" not in page.url:
        page.goto(TEACHER_BASE + "#/pages/questions/index", wait_until="domcontentloaded", timeout=15_000)
    expect(page.get_by_text("学生提问", exact=True)).to_be_visible(timeout=10_000)
    expect(page.get_by_text(marker, exact=True)).to_be_visible(timeout=30_000)
    expect(page.get_by_text(re.compile("待处理|pending"), exact=False)).to_be_visible(timeout=10_000)
    token = page.evaluate("localStorage.getItem('v2-token')")
    if token:
        save_state({"teacher_token": token})
    _screenshot(page, "teacher-question-list.png")
    request.node._smoke_notes = "教师问题列表可见该 pending 会话"
    context.close()


@pytest.mark.smoke_meta(idx=5, name="Cleanup")
def test_05_cleanup_best_effort(playwright, request):
    state = load_state()
    conv_id = state.get("conversation_id")
    token = state.get("teacher_token")
    if not conv_id or not token:
        note = f"WARN: cleanup skipped, manually delete question id={conv_id}"
        print(note)
        save_state({"cleanup_note": note})
        request.node._smoke_notes = note
        pytest.skip(note)

    api = playwright.request.new_context(
        base_url=TEACHER_BASE,
        extra_http_headers={"Authorization": f"Bearer {token}"},
    )
    try:
        accept = api.post(f"/api/conversations/{conv_id}/accept")
        resolve = api.post(f"/api/conversations/{conv_id}/resolve")
        if accept.status not in (200, 400, 409) or resolve.status not in (200, 400, 409):
            note = f"WARN: cleanup skipped, manually delete question id={conv_id}"
            print(note)
            save_state({"cleanup_note": note})
            pytest.skip(note)
        note = f"accepted/resolved conversation id={conv_id}"
        save_state({"cleanup_note": note})
        request.node._smoke_notes = note
    finally:
        api.dispose()
