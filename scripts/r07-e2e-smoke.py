#!/usr/bin/env python3
"""
R07 端到端验收脚本 · 针对 192.168.100.165:8100

覆盖：
- R07-1 教师 HTTP 发消息（teacher_serving 下）
- R07-2 AI 暂停/恢复（pending_teacher/teacher_serving 不调 Dify、resolved 触发 reactivate、closed 守卫）
- R07-3 escalate 时广播学院教师工单通知（admin 不收）

只依赖 httpx + websockets。

退出码：0 = 全 PASS；非 0 = 某步失败。
"""
import asyncio
import json
import sys
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
import websockets

BASE = "http://192.168.100.165:8100"
WS_BASE = "ws://192.168.100.165:8100"

STUDENT = {"staff_id": "2024010001", "password": "2024010001"}
TEACHER = {"staff_id": "T001", "password": "liangshufeng"}
ADMIN = {"staff_id": "A001", "password": "admin123"}

# ========== 公共工具 ==========

PASS_COUNT = 0
FAIL_COUNT = 0
FAIL_DETAILS: list[str] = []


def _log_result(name: str, ok: bool, detail: str = ""):
    global PASS_COUNT, FAIL_COUNT
    icon = "[PASS]" if ok else "[FAIL]"
    line = f"{icon} {name}"
    if detail:
        line += f" -- {detail}"
    print(line)
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
        FAIL_DETAILS.append(line)


def login(client: httpx.Client, creds: dict) -> str:
    r = client.post(f"{BASE}/api/auth/login", json=creds)
    r.raise_for_status()
    return r.json()["access_token"]


@asynccontextmanager
async def ws_connect(token: str, label: str):
    uri = f"{WS_BASE}/ws?token={token}"
    ws = await websockets.connect(uri)
    print(f"  WS {label}: connected")
    try:
        yield ws
    finally:
        await ws.close()
        print(f"  WS {label}: closed")


async def drain_messages(ws, seconds: float = 0.5) -> list[dict]:
    """把 ws 上已到达的消息全部拉出来，不阻塞"""
    events = []
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=max(0.05, end - time.monotonic()))
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                events.append({"raw": raw})
        except asyncio.TimeoutError:
            break
    return events


async def wait_for_event(ws, event_type: str, timeout: float = 5.0, predicate=None) -> dict | None:
    """等待指定 type 的事件（可选 predicate 进一步筛）"""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - time.monotonic()))
        except asyncio.TimeoutError:
            return None
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if msg.get("type") != event_type:
            continue
        if predicate and not predicate(msg):
            continue
        return msg
    return None


# ========== 主流程 ==========

async def main() -> int:
    print("=" * 70)
    print("R07 End-to-End Smoke Test | target =", BASE)
    print("=" * 70)

    # ---------- 登录 ----------
    with httpx.Client(timeout=10.0) as client:
        try:
            student_token = login(client, STUDENT)
            teacher_token = login(client, TEACHER)
            admin_token = login(client, ADMIN)
        except httpx.HTTPStatusError as e:
            _log_result("login (all three)", False, str(e))
            return 1
    _log_result("login (student/teacher/admin)", True)

    s_hdr = {"Authorization": f"Bearer {student_token}"}
    t_hdr = {"Authorization": f"Bearer {teacher_token}"}

    async with httpx.AsyncClient(timeout=30.0) as http:
        # ---------- 建会话 ----------
        r = await http.post(f"{BASE}/api/conversations", headers=s_hdr,
                            json={"title": "r07 e2e smoke"})
        if r.status_code != 201:
            _log_result("create conversation", False, f"status={r.status_code} body={r.text[:200]}")
            return 1
        conv_id = r.json()["id"]
        _log_result("create conversation", True, f"conv_id={conv_id}")

        # ---------- 同时接入 3 个 WS ----------
        async with ws_connect(student_token, "student") as ws_s, \
                   ws_connect(teacher_token, "teacher") as ws_t, \
                   ws_connect(admin_token, "admin") as ws_a:
            # 学生加入会话房间
            await ws_s.send(json.dumps({"type": "join_room", "data": {"conv_id": conv_id}}))
            msg = await wait_for_event(ws_s, "room_joined", timeout=3)
            _log_result("student joins conv room", msg is not None,
                        f"room_joined for conv_id={msg['data']['conv_id']}" if msg else "no room_joined")

            # 清空启动期残留事件
            await drain_messages(ws_s, 0.3)
            await drain_messages(ws_t, 0.3)
            await drain_messages(ws_a, 0.3)

            # =================================================================
            # 阶段 A · ai_serving 正向对照（验证 Dify 在 ai_serving 下可用）
            # =================================================================
            print("\n--- 阶段 A · ai_serving SSE ---")
            async with http.stream("POST", f"{BASE}/api/chat/send",
                                   headers=s_hdr,
                                   json={"conv_id": conv_id, "content": "介绍一下校园卡办理流程"}) as resp:
                content_type = resp.headers.get("content-type", "")
                _log_result("A.1 /chat/send returns SSE in ai_serving",
                            "event-stream" in content_type,
                            f"content-type={content_type}")
                # 读一点流确认真的在推送
                got_message_end = False
                got_any_chunk = False
                async for chunk in resp.aiter_text():
                    if not chunk:
                        continue
                    got_any_chunk = True
                    if "message_end" in chunk or "done" in chunk:
                        got_message_end = True
                        break
                _log_result("A.2 SSE streams at least one chunk", got_any_chunk)
                _log_result("A.3 SSE reaches message_end/done", got_message_end)

            # 清理阶段 A 所有 ws 的信息（ai_serving 期间学生房间可能有 new_message 广播）
            await drain_messages(ws_s, 0.3)
            await drain_messages(ws_t, 0.3)
            await drain_messages(ws_a, 0.3)

            # =================================================================
            # 阶段 B · escalate 广播通知（R07-3）
            # =================================================================
            print("\n--- 阶段 B · escalate / escalation_notify (R07-3) ---")
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/escalate", headers=s_hdr)
            _log_result("B.1 escalate returns 200", r.status_code == 200,
                        f"status={r.status_code}")
            body = r.json() if r.status_code == 200 else {}
            _log_result("B.2 status = pending_teacher",
                        body.get("status") == "pending_teacher",
                        f"status={body.get('status')}")

            # escalate 返回后，WS 消息应很快到达。给 1s 缓冲后一次性 drain 三个 ws。
            await asyncio.sleep(1.0)
            teacher_events = await drain_messages(ws_t, 0.3)
            student_events = await drain_messages(ws_s, 0.3)
            admin_events = await drain_messages(ws_a, 0.3)

            notify = next((e for e in teacher_events
                           if e.get("type") == "escalation_notify"
                           and e.get("data", {}).get("conv_id") == conv_id), None)
            _log_result("B.3 teacher receives escalation_notify", notify is not None,
                        f"teacher_events={[e.get('type') for e in teacher_events]}" if not notify else "")
            if notify:
                data = notify.get("data", {})
                required = {"conv_id", "student_id", "title", "status", "created_at"}
                missing = required - data.keys()
                _log_result("B.4 escalation_notify payload has all required fields",
                            not missing,
                            f"missing={missing}" if missing else "conv_id/student_id/title/status/created_at OK")
                _log_result("B.5 escalation_notify status = pending_teacher",
                            data.get("status") == "pending_teacher",
                            f"status={data.get('status')}")

            status_change = next((e for e in student_events
                                  if e.get("type") == "status_changed"
                                  and e.get("data", {}).get("status") == "pending_teacher"), None)
            _log_result("B.6 student conv room receives status_changed=pending_teacher",
                        status_change is not None)

            admin_got_notify = any(e.get("type") == "escalation_notify" for e in admin_events)
            _log_result("B.7 admin does NOT receive escalation_notify",
                        not admin_got_notify,
                        f"admin_events={[e.get('type') for e in admin_events]}" if admin_got_notify else "")

            # =================================================================
            # 阶段 C · pending_teacher 下学生 /chat/send 不调 Dify（R07-2）
            # =================================================================
            print("\n--- 阶段 C · pending_teacher /chat/send = JSON, no Dify (R07-2) ---")
            r = await http.post(f"{BASE}/api/chat/send",
                                headers=s_hdr,
                                json={"conv_id": conv_id, "content": "老师接单前我补充一下"})
            _log_result("C.1 /chat/send returns 200 in pending_teacher",
                        r.status_code == 200, f"status={r.status_code}")
            content_type = r.headers.get("content-type", "")
            _log_result("C.2 /chat/send returns JSON (not SSE)",
                        "application/json" in content_type and "event-stream" not in content_type,
                        f"content-type={content_type}")
            body = r.json() if "application/json" in content_type else {}
            _log_result("C.3 response has sender_type=student",
                        body.get("sender_type") == "student",
                        f"sender_type={body.get('sender_type')}")

            # 清理学生房间残留
            await drain_messages(ws_s, 0.3)

            # =================================================================
            # 阶段 D · 教师接单 + 真人发消息（R07-1）
            # =================================================================
            print("\n--- 阶段 D · accept + teacher sends message (R07-1) ---")
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/accept", headers=t_hdr)
            _log_result("D.1 teacher accept returns 200",
                        r.status_code == 200, f"status={r.status_code}")
            body = r.json() if r.status_code == 200 else {}
            _log_result("D.2 status = teacher_serving",
                        body.get("status") == "teacher_serving",
                        f"status={body.get('status')}")

            # 学生房间应收到 status_changed=teacher_serving
            ev = await wait_for_event(ws_s, "status_changed", timeout=3,
                                      predicate=lambda m: m.get("data", {}).get("status") == "teacher_serving")
            _log_result("D.3 student receives status_changed=teacher_serving", ev is not None)

            # 教师发消息
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/messages",
                                headers=t_hdr,
                                json={"content": "你好，我是值班老师，关于你的校园卡问题……"})
            _log_result("D.4 teacher POST /messages returns 201",
                        r.status_code == 201, f"status={r.status_code}")
            body = r.json() if r.status_code in (200, 201) else {}
            _log_result("D.5 response sender_type=teacher",
                        body.get("sender_type") == "teacher")

            # 学生收到 new_message (sender_type=teacher)
            ev = await wait_for_event(ws_s, "new_message", timeout=3,
                                      predicate=lambda m: m.get("data", {}).get("sender_type") == "teacher")
            _log_result("D.6 student receives new_message with sender_type=teacher",
                        ev is not None)
            if ev:
                _log_result("D.7 new_message has sender_id",
                            ev["data"].get("sender_id") is not None,
                            f"sender_id={ev['data'].get('sender_id')}")

            # =================================================================
            # 阶段 E · teacher_serving 下学生 /chat/send 也是 JSON（R07-2）
            # =================================================================
            print("\n--- 阶段 E · teacher_serving /chat/send = JSON (R07-2) ---")
            r = await http.post(f"{BASE}/api/chat/send",
                                headers=s_hdr,
                                json={"conv_id": conv_id, "content": "老师处理中我补充一下"})
            content_type = r.headers.get("content-type", "")
            _log_result("E.1 /chat/send returns JSON (not SSE) in teacher_serving",
                        r.status_code == 200 and "event-stream" not in content_type,
                        f"status={r.status_code} content-type={content_type}")

            await drain_messages(ws_s, 0.3)

            # =================================================================
            # 阶段 F · resolve + 学生下次消息触发 reactivate（R07-2 核心）
            # =================================================================
            print("\n--- 阶段 F · resolve + next-message reactivate (R07-2) ---")
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/resolve", headers=t_hdr)
            _log_result("F.1 teacher resolve returns 200", r.status_code == 200)
            ev = await wait_for_event(ws_s, "status_changed", timeout=3,
                                      predicate=lambda m: m.get("data", {}).get("status") == "resolved")
            _log_result("F.2 student receives status_changed=resolved", ev is not None)

            # 学生发 /chat/send，应当：先 WS 收到 status_changed(ai_serving, previous_status=resolved)，再 SSE
            got_reactivate_event = False
            sse_after = False
            reactivate_task = asyncio.create_task(
                wait_for_event(ws_s, "status_changed", timeout=8,
                               predicate=lambda m: (m.get("data", {}).get("status") == "ai_serving"
                                                    and m.get("data", {}).get("previous_status") == "resolved"))
            )
            async with http.stream("POST", f"{BASE}/api/chat/send",
                                   headers=s_hdr,
                                   json={"conv_id": conv_id, "content": "解决后我还有个追加问题"}) as resp:
                content_type = resp.headers.get("content-type", "")
                sse_after = "event-stream" in content_type
                # 读取一点流，确保有 AI 回复
                async for chunk in resp.aiter_text():
                    if not chunk:
                        continue
                    if "message_end" in chunk or "done" in chunk:
                        break
            reactivate_msg = await reactivate_task
            got_reactivate_event = reactivate_msg is not None

            _log_result("F.3 /chat/send returns SSE after reactivate", sse_after)
            _log_result("F.4 student WS receives status_changed(ai_serving, previous_status=resolved)",
                        got_reactivate_event)

            # =================================================================
            # 阶段 G · /messages 在 resolved 下也会先 reactivate（R07-2 守卫）
            # =================================================================
            print("\n--- 阶段 G · /messages resolved => reactivate + JSON (R07-2) ---")
            # 让会话回到 resolved：教师 re-accept 后再 resolve
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/escalate", headers=s_hdr)
            # escalate 需要 ai_serving -> pending_teacher
            if r.status_code == 200:
                r = await http.post(f"{BASE}/api/conversations/{conv_id}/accept", headers=t_hdr)
                r = await http.post(f"{BASE}/api/conversations/{conv_id}/resolve", headers=t_hdr)
            # 清残留
            await drain_messages(ws_s, 0.5)
            await drain_messages(ws_t, 0.3)

            # 学生从 resolved 通过 /messages 发消息
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/messages",
                                headers=s_hdr,
                                json={"content": "通过 /messages 触发恢复"})
            _log_result("G.1 student /messages returns 201 in resolved",
                        r.status_code == 201, f"status={r.status_code}")
            content_type = r.headers.get("content-type", "")
            _log_result("G.2 /messages returns JSON (not SSE)",
                        "application/json" in content_type and "event-stream" not in content_type,
                        f"content-type={content_type}")

            # 学生 WS 应先看到 status_changed(ai_serving, previous_status=resolved)，再看到 new_message
            evs = await drain_messages(ws_s, 1.5)
            status_idx = next((i for i, e in enumerate(evs)
                               if e.get("type") == "status_changed"
                               and e.get("data", {}).get("status") == "ai_serving"
                               and e.get("data", {}).get("previous_status") == "resolved"), -1)
            new_msg_idx = next((i for i, e in enumerate(evs)
                                if e.get("type") == "new_message"
                                and e.get("data", {}).get("sender_type") == "student"), -1)
            _log_result("G.3 WS receives status_changed(ai_serving, previous_status=resolved)",
                        status_idx >= 0)
            _log_result("G.4 WS receives new_message after status_changed",
                        new_msg_idx > status_idx,
                        f"status_idx={status_idx}, new_msg_idx={new_msg_idx}, types={[e.get('type') for e in evs]}")

            # =================================================================
            # 阶段 H · closed 守卫 (R07-2 边界)
            # =================================================================
            print("\n--- 阶段 H · closed guard on /messages (R07-2) ---")
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/close", headers=s_hdr)
            _log_result("H.1 close returns 200", r.status_code == 200)
            r = await http.post(f"{BASE}/api/conversations/{conv_id}/messages",
                                headers=s_hdr,
                                json={"content": "关闭后仍尝试发送"})
            _log_result("H.2 /messages in closed returns 403",
                        r.status_code == 403, f"status={r.status_code} body={r.text[:200]}")
            if r.status_code == 403:
                body = r.json()
                _log_result("H.3 error detail mentions 关闭",
                            "关闭" in body.get("detail", ""),
                            f"detail={body.get('detail')}")

            # =================================================================
            # 阶段 I · R07-1 空白内容拒绝（schema 层）
            # =================================================================
            print("\n--- 阶段 I · blank-content rejection (R07-1 schema) ---")
            r2 = await http.post(f"{BASE}/api/conversations",
                                 headers=s_hdr, json={"title": "blank test"})
            if r2.status_code == 201:
                blank_conv_id = r2.json()["id"]
                for raw in ["", "   ", "\n\t"]:
                    r = await http.post(f"{BASE}/api/conversations/{blank_conv_id}/messages",
                                        headers=s_hdr, json={"content": raw})
                    _log_result(f"I.{'blank' if not raw.strip() else 'ws'}-content {raw!r} => 422",
                                r.status_code == 422,
                                f"status={r.status_code}")

    # ---------- 汇总 ----------
    print("\n" + "=" * 70)
    print(f"SUMMARY: PASS={PASS_COUNT}  FAIL={FAIL_COUNT}")
    if FAIL_DETAILS:
        print("\nFailed assertions:")
        for d in FAIL_DETAILS:
            print(f"  {d}")
        print("=" * 70)
        return 1
    print("ALL R07 E2E ASSERTIONS PASSED ✓")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
