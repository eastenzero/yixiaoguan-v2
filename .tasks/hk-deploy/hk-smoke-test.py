#!/usr/bin/env python3
import json
import sys
import time
import warnings
from dataclasses import dataclass
from typing import Any

import requests

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

ORIGIN = "https://yxg.130814.xyz"
STUDENT_H5 = "https://yxg.130814.xyz/"
TEACHER_H5 = "https://teacher.130814.xyz/"
API = f"{ORIGIN}/api"

STUDENT = {"staff_id": "4125150001", "password": "4125150001", "name": "黄静"}
TEACHER = {"staff_id": "anjing", "password": "Anjing@yxg2026", "name": "安静"}


@dataclass
class Result:
    index: int
    item: str
    passed: bool
    note: str = ""


class SmokeTest:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.verify = False
        self.results: list[Result] = []
        self.student_token: str | None = None
        self.teacher_token: str | None = None
        self.cleanup_conv_ids: list[str] = []

    def record(self, item: str, passed: bool, note: str = "") -> bool:
        result = Result(len(self.results) + 1, item, passed, note)
        self.results.append(result)
        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {item} - {note}")
        return passed

    def request(self, method: str, url: str, token: str | None = None, **kwargs: Any) -> requests.Response:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        headers.setdefault("Accept", "application/json")
        return self.session.request(method, url, headers=headers, timeout=60, **kwargs)

    @staticmethod
    def json_or_text(resp: requests.Response) -> Any:
        try:
            return resp.json()
        except ValueError:
            return resp.text

    @staticmethod
    def nested(data: Any, *keys: str) -> Any:
        current = data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    @staticmethod
    def find_first(data: Any, keys: set[str]) -> Any:
        if isinstance(data, dict):
            for key, value in data.items():
                if key in keys and value not in (None, ""):
                    return value
            for value in data.values():
                found = SmokeTest.find_first(value, keys)
                if found not in (None, ""):
                    return found
        elif isinstance(data, list):
            for value in data:
                found = SmokeTest.find_first(value, keys)
                if found not in (None, ""):
                    return found
        return None

    def login(self, account: dict[str, str], role: str) -> str | None:
        resp = self.request("POST", f"{API}/auth/login", json={
            "staff_id": account["staff_id"],
            "password": account["password"],
        })
        data = self.json_or_text(resp)
        token = self.find_first(data, {"access_token", "token"})
        ok = resp.status_code == 200 and isinstance(token, str) and bool(token)
        self.record(f"{role}登录", ok, f"HTTP {resp.status_code}")
        return token if ok else None

    def auth_me(self, token: str | None, expected_name: str, role: str) -> None:
        if not token:
            self.record(f"{role} /auth/me", False, "缺少 token")
            return
        resp = self.request("GET", f"{API}/auth/me", token=token)
        data = self.json_or_text(resp)
        name = self.find_first(data, {"name", "real_name", "username"})
        self.record(
            f"{role} /auth/me",
            resp.status_code == 200 and name == expected_name,
            f"HTTP {resp.status_code}, name={name!r}",
        )

    def create_conversation(self, token: str, title: str) -> str | None:
        resp = self.request("POST", f"{API}/conversations", token=token, json={"title": title})
        data = self.json_or_text(resp)
        conv_id = self.find_first(data, {"id", "conv_id", "conversation_id"})
        ok = resp.status_code in (200, 201) and conv_id is not None
        self.record(f"创建会话：{title}", ok, f"HTTP {resp.status_code}, id={conv_id}")
        if ok:
            conv_id = str(conv_id)
            self.cleanup_conv_ids.append(conv_id)
            return conv_id
        return None

    def send_chat(self, token: str, conv_id: str, content: str) -> tuple[bool, str]:
        try:
            resp = self.session.post(
                f"{API}/chat/send",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "text/event-stream",
                    "Content-Type": "application/json",
                },
                json={"conv_id": conv_id, "content": content},
                stream=True,
                timeout=(20, 180),
                verify=False,
            )
        except requests.RequestException as exc:
            return False, f"请求异常：{exc}"

        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:300]}"

        full_content = ""
        chunks: list[str] = []
        current_event = ""
        start = time.time()

        for raw_line in resp.iter_lines(decode_unicode=True):
            if time.time() - start > 180:
                return False, "SSE 超时"
            if raw_line is None:
                continue
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
                continue
            if not line.startswith("data:"):
                continue

            payload = line.split(":", 1)[1].strip()
            if payload == "[DONE]":
                break
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                chunks.append(payload)
                continue

            event = data.get("event") or data.get("type") or current_event
            if event == "message_end":
                full_content = (
                    data.get("full_content")
                    or data.get("answer")
                    or data.get("content")
                    or self.nested(data, "data", "full_content")
                    or full_content
                )
            else:
                piece = (
                    data.get("answer")
                    or data.get("content")
                    or data.get("text")
                    or self.nested(data, "data", "answer")
                    or self.nested(data, "data", "content")
                )
                if isinstance(piece, str):
                    chunks.append(piece)

        answer = full_content or "".join(chunks)
        return bool(answer.strip()), answer.strip()

    def run_health_and_auth(self) -> None:
        resp = self.request("GET", f"{ORIGIN}/health")
        self.record("基础健康检查 /health", resp.status_code == 200, f"HTTP {resp.status_code}")

        self.student_token = self.login(STUDENT, "学生")
        self.auth_me(self.student_token, STUDENT["name"], "学生")

        self.teacher_token = self.login(TEACHER, "辅导员")
        self.auth_me(self.teacher_token, TEACHER["name"], "辅导员")

    def run_rag(self) -> None:
        if not self.student_token:
            self.record("AI 对话", False, "缺少学生 token")
            return
        conv_id = self.create_conversation(self.student_token, "smoke-test-rag")
        if not conv_id:
            return

        checks = [
            ("宿舍电费怎么交？", lambda s: "完美校园" in s or "充值" in s, "包含“完美校园”或“充值”"),
            ("国家奖学金有哪些？", lambda s: "10000" in s or "奖学金" in s, "包含“10000”或“奖学金”"),
            ("图书馆开放时间？", lambda s: len(s) > 50, "回答长度 > 50"),
        ]
        for question, predicate, expectation in checks:
            ok, answer = self.send_chat(self.student_token, conv_id, question)
            passed = ok and predicate(answer)
            self.record(f"AI 对话：{question}", passed, f"{expectation}; 回答片段={answer[:120]!r}")

    def run_teacher_flow(self) -> None:
        if not self.student_token or not self.teacher_token:
            self.record("学生转交辅导员流程", False, "缺少学生或辅导员 token")
            return

        conv_id = self.create_conversation(self.student_token, "smoke-test-escalation")
        if not conv_id:
            return

        ok, answer = self.send_chat(self.student_token, conv_id, "【smoke-test】请问毕业证什么时候发？")
        self.record("转交流程：学生发送初始消息", ok, f"回答片段={answer[:120]!r}")

        resp = self.request("POST", f"{API}/conversations/{conv_id}/escalate", token=self.student_token)
        self.record("转交流程：学生转交辅导员", resp.status_code in (200, 201), f"HTTP {resp.status_code}")

        resp = self.request("GET", f"{API}/conversations", token=self.teacher_token)
        data = self.json_or_text(resp)
        visible = str(conv_id) in json.dumps(data, ensure_ascii=False)
        status_note = self.find_first(data, {"status", "state"})
        self.record("转交流程：辅导员会话列表可见", resp.status_code == 200 and visible, f"HTTP {resp.status_code}, status={status_note!r}")

        resp = self.request("POST", f"{API}/conversations/{conv_id}/accept", token=self.teacher_token)
        self.record("转交流程：辅导员接受", resp.status_code in (200, 201), f"HTTP {resp.status_code}")

        resp = self.request(
            "POST",
            f"{API}/conversations/{conv_id}/messages",
            token=self.teacher_token,
            json={"content": "毕业证6月底发放"},
        )
        self.record("转交流程：辅导员回复", resp.status_code in (200, 201), f"HTTP {resp.status_code}")

        resp = self.request("POST", f"{API}/conversations/{conv_id}/resolve", token=self.teacher_token)
        self.record("转交流程：辅导员关闭", resp.status_code in (200, 201), f"HTTP {resp.status_code}")

        detail_resp = self.request("GET", f"{API}/conversations/{conv_id}", token=self.student_token)
        messages_resp = self.request("GET", f"{API}/conversations/{conv_id}/messages", token=self.student_token)
        detail_data = self.json_or_text(detail_resp)
        messages_data = self.json_or_text(messages_resp)
        has_reply = (
            "毕业证6月底发放" in json.dumps(detail_data, ensure_ascii=False)
            or "毕业证6月底发放" in json.dumps(messages_data, ensure_ascii=False)
        )
        self.record(
            "转交流程：学生可见辅导员回复",
            detail_resp.status_code == 200 and messages_resp.status_code == 200 and has_reply,
            f"detail HTTP {detail_resp.status_code}, messages HTTP {messages_resp.status_code}",
        )

        resp = self.request("GET", f"{API}/conversations/unread-summary", token=self.student_token)
        data = self.json_or_text(resp)
        has_unread = any(isinstance(x, int) and x > 0 for x in self.flatten(data))
        self.record("转交流程：学生未读统计", resp.status_code == 200 and has_unread, f"HTTP {resp.status_code}, body={str(data)[:160]}")

    @staticmethod
    def flatten(data: Any) -> list[Any]:
        if isinstance(data, dict):
            values: list[Any] = []
            for value in data.values():
                values.extend(SmokeTest.flatten(value))
            return values
        if isinstance(data, list):
            values = []
            for value in data:
                values.extend(SmokeTest.flatten(value))
            return values
        return [data]

    def run_knowledge(self) -> None:
        if not self.teacher_token:
            self.record("知识库接口", False, "缺少辅导员 token")
            return

        resp = self.request("GET", f"{API}/v1/knowledge/unanswered-top", token=self.teacher_token)
        unanswered_data = self.json_or_text(resp)
        self.record("知识库：未回答排行", resp.status_code == 200, f"HTTP {resp.status_code}")

        unanswered_id = None
        if isinstance(unanswered_data, dict):
            items = unanswered_data.get("items")
            if isinstance(items, list) and items:
                unanswered_id = items[0].get("id")

        if not unanswered_id:
            self.record("知识库：提交测试草稿", False, "未回答排行为空，无法取得 unanswered_question_id")
            return

        resp = self.request(
            "POST",
            f"{API}/v1/knowledge/drafts",
            token=self.teacher_token,
            json={
                "unanswered_question_id": unanswered_id,
                "raw_answer": "smoke-test-draft 测试内容",
                "scope": "college",
            },
        )
        self.record("知识库：提交测试草稿", resp.status_code in (200, 201), f"HTTP {resp.status_code}, body={resp.text[:160]}")

    def run_frontend(self) -> None:
        for name, url in (("学生端首页", STUDENT_H5), ("教师端首页", TEACHER_H5)):
            resp = self.session.get(url, timeout=60, verify=False)
            body = resp.text.lower()
            self.record(f"前端可达性：{name}", resp.status_code == 200 and "html" in body, f"HTTP {resp.status_code}")

    def cleanup(self) -> None:
        for conv_id in self.cleanup_conv_ids:
            for token, action in (
                (self.teacher_token, "resolve"),
                (self.teacher_token, "close"),
                (self.student_token, "close"),
            ):
                if not token:
                    continue
                try:
                    resp = self.request("POST", f"{API}/conversations/{conv_id}/{action}", token=token)
                    if resp.status_code in (200, 201):
                        break
                except requests.RequestException:
                    pass

    def print_summary(self) -> None:
        print("\n| # | 测试项 | 结果 | 备注 |")
        print("|---|--------|------|------|")
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            note = result.note.replace("\n", " ").replace("|", "\\|")
            print(f"| {result.index} | {result.item} | {status} | {note} |")

        if all(result.passed for result in self.results):
            print("\n✅ HK 环境冒烟测试全部通过，可以启动内测")
        else:
            print("\n❌ HK 环境冒烟测试存在失败项，请根据上表排查")

    def run(self) -> int:
        try:
            self.run_health_and_auth()
            self.run_rag()
            self.run_teacher_flow()
            self.run_knowledge()
            self.run_frontend()
        finally:
            self.cleanup()
            self.print_summary()
        return 0 if all(result.passed for result in self.results) else 1


if __name__ == "__main__":
    sys.exit(SmokeTest().run())
