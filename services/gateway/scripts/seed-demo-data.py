#!/usr/bin/env python3
"""
医小管 v2 — Demo/演示数据 seed 脚本
====================================

把假 conversation / message / kb_suggestion 注入 165 dev backend，让 dashboard
工单列表 / 知识库 看起来饱满；演示完成后用 cleanup 模式一键回滚。

✦ 强约束（按用户要求）✦
  - 只允许在 dev/staging 跑，**严禁** prod
    - 通过 `APP_ENV` 环境变量识别（=prod/production 直接退出）
    - 通过 `GATEWAY_URL` 黑名单识别（命中已知 prod 域名 / 公网 IP 直接退出）
  - 所有写入都打上 `[demo]` 前缀作为可追溯 marker，cleanup 只回滚带 marker 的行
  - 不修改任何生产模型 / 不触碰 migration / 不需要修改后端代码即可跑

✦ 工作模式 ✦
  conv          基于 HTTP API 创建 conversation + messages（推荐主路径）
                走真实状态机 ai_serving → pending_teacher → teacher_serving → resolved
  kb-sql        生成 INSERT INTO kb_suggestions / unanswered_questions 的 SQL（stdout）
                用法：python seed-demo-data.py kb-sql --kb-count 25 | ssh easten@192.168.100.165 \\
                       'docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2'
  cleanup-sql   生成 DELETE FROM ... WHERE ... LIKE '[demo]%' 的 SQL（stdout）
                用法：python seed-demo-data.py cleanup-sql | ssh easten@192.168.100.165 \\
                       'docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2'
  list-sql      生成 SELECT 计数 / 抽样的 SQL（stdout）

✦ 安装 ✦
  pip install faker requests

✦ 快速演示 ✦
  # 1. dev 灌 60 条 conversation
  python services/gateway/scripts/seed-demo-data.py conv --count 60 --confirm

  # 2. dev 灌 25 条 KB 待审 + 已审 entries（管理员视角看到）
  python services/gateway/scripts/seed-demo-data.py kb-sql --kb-count 25 | \\
    ssh easten@192.168.100.165 'docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2'

  # 3. 演示结束清理
  python services/gateway/scripts/seed-demo-data.py cleanup-sql | \\
    ssh easten@192.168.100.165 'docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2'
"""
from __future__ import annotations

import argparse
import io
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

# Windows 默认 locale 是 GBK / cp936，会把中文 print 当 GBK 编出去，
# 通过管道喂给 postgres (UTF-8) 时炸 "invalid byte sequence"。
# 全程强制 UTF-8 stdout。
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")  # type: ignore[assignment]

try:
    import requests
except ImportError:
    sys.exit("缺少 requests，请：pip install requests faker")

try:
    from faker import Faker
except ImportError:
    sys.exit("缺少 faker，请：pip install requests faker")


DEMO_MARKER = "[demo]"

# ─── prod 黑名单：命中任意一项直接退出 ─────────────────────────────
PROD_HOST_PATTERNS = [
    r".*xiaoguan\.site$",
    r".*130814\.xyz$",
    r"^64\.90\.13\.65$",
    r"^60\.205\.205\.99$",
    r"^82\.156\.129\.75$",
]
# 允许的开发环境（这些必须显式 in 列表才能跑写入操作）
DEV_HOST_PATTERNS = [
    r"^192\.168\.\d+\.\d+$",
    r"^127\.0\.0\.1$",
    r"^localhost$",
    r"^10\.\d+\.\d+\.\d+$",
]


def _host_matches(host: str, patterns: list[str]) -> bool:
    return any(re.match(p, host) for p in patterns)


def _enforce_non_prod(gateway_url: str) -> None:
    app_env = (os.getenv("APP_ENV") or "dev").lower()
    if app_env in {"prod", "production"}:
        sys.exit(f"❌ 拒绝执行：APP_ENV={app_env}（seed 脚本严禁在 prod 跑）")

    parsed = urlparse(gateway_url)
    host = parsed.hostname or ""
    if _host_matches(host, PROD_HOST_PATTERNS):
        sys.exit(
            f"❌ 拒绝执行：gateway host '{host}' 命中 prod 黑名单。"
            f"\n   黑名单：{PROD_HOST_PATTERNS}"
            f"\n   要在 prod 上跑请修改源码（不推荐），或先开发 prod 专用 admin tooling。"
        )
    if not _host_matches(host, DEV_HOST_PATTERNS):
        sys.exit(
            f"❌ 拒绝执行：gateway host '{host}' 不在 DEV 白名单里。"
            f"\n   白名单：{DEV_HOST_PATTERNS}"
            f"\n   误判？把 host 加入 DEV_HOST_PATTERNS 或导出 APP_ENV=staging。"
            if app_env != "staging" else
            f"❌ 拒绝执行：staging 模式仍要求 host '{host}' ∈ DEV_HOST_PATTERNS"
        )


# ─── HTTP API client (conv mode) ──────────────────────────────────
@dataclass
class Client:
    base: str
    session: requests.Session
    token: Optional[str] = None
    user_id: Optional[int] = None

    @classmethod
    def login(cls, base: str, staff_id: str, password: str) -> "Client":
        sess = requests.Session()
        sess.headers["Content-Type"] = "application/json"
        c = cls(base=base, session=sess)
        r = sess.post(f"{base}/api/auth/login", json={"staff_id": staff_id, "password": password}, timeout=10)
        if r.status_code != 200:
            raise RuntimeError(f"login failed for {staff_id}: {r.status_code} {r.text[:200]}")
        data = r.json()
        c.token = data["access_token"]
        sess.headers["Authorization"] = f"Bearer {c.token}"
        me = sess.get(f"{base}/api/auth/me", timeout=10).json()
        c.user_id = me.get("id")
        return c

    def post(self, path: str, json: dict | None = None) -> requests.Response:
        return self.session.post(f"{self.base}{path}", json=json, timeout=15)

    def get(self, path: str, params: dict | None = None) -> requests.Response:
        return self.session.get(f"{self.base}{path}", params=params, timeout=15)


# ─── Faker pools (zh_CN) ──────────────────────────────────────────
fake = Faker("zh_CN")
fake.seed_instance(42)  # 可复现

# 真实场景化的学生提问模板 — 围绕选课 / 宿舍 / 奖学金 / 实习 / 食堂 / 体测 / 论文
QUESTION_TEMPLATES = [
    "老师好，{topic}，{detail}",
    "请问{topic}是怎么处理的？{detail}",
    "我想咨询一下关于{topic}的事情，{detail}",
    "我有个疑问，{topic}，希望老师能解答 {detail}",
    "想麻烦老师确认下，{topic}，{detail}",
]
TOPICS = [
    ("选课系统什么时候开放", "下学期的专业选修课我还没看到选课入口"),
    ("宿舍调换需要走什么流程", "我和同寝关系不太好想调宿舍"),
    ("奖学金申请截止日期", "听说今年要补一份家庭情况证明"),
    ("毕业实习证明在哪里盖章", "我已经实习一个月了想先拿证明"),
    ("学费缴纳是否可以分期", "今年学费有点紧张"),
    ("补办学生证的流程", "之前把学生证弄丢了"),
    ("第三餐厅几点关门", "晚上自习回去经常买不到饭"),
    ("体测不及格能补测吗", "上次发烧没考好"),
    ("毕业论文格式要求在哪下载", "搜了官网没找到模板"),
    ("PE 老师签到二维码扫不出来", "今天体育课点不了名"),
    ("社团报名延期了吗", "校园开放日错过了截止时间"),
    ("校医院能开转诊证明吗", "想去市三院做个进一步检查"),
    ("英语六级报名什么时候", "想了解下今年的安排"),
    ("辅修申请已经提交了多久没回复", "上周一交的材料"),
    ("课表里有冲突怎么办", "选了两门同一时间的"),
    ("校园卡丢了挂失要多久", "怕被人盗刷"),
    ("申请助学金需要什么材料", "想提前准备"),
    ("校园网账号是和学号一样吗", "新生入学想连一下"),
    ("教学楼几点锁门", "经常自习到很晚"),
    ("学校有没有心理咨询预约", "最近压力比较大"),
    ("延毕一年需要哪些手续", "想多刷个证书再毕业"),
    ("党课报名什么时候开始", "想入党"),
    ("出国交流项目去哪个学院问", "对德国那边感兴趣"),
    ("校历期末考试周从几号开始", "需要订回家车票"),
]

AI_REPLY_TEMPLATES = [
    "根据{college_name}的常见答复，{advice}。如有疑问可以直接呼叫老师 ✋",
    "已为您查到：{advice}。如果信息不准确请向老师反馈，方便我们持续完善。",
    "您好，{advice}。建议优先联系院系教务老师确认时效。",
    "您提到的问题，{advice}。系统暂未匹配到完全一致的政策条款，建议人工核实。",
]
AI_ADVICE = [
    "通常需要先在校务系统提交申请，由辅导员审核后转教务",
    "请关注学院公众号置顶推送，时间窗口一般在每月 1-10 号",
    "申请材料包括身份证复印件、学生证、近期免冠照",
    "可联系院办 0531-xxxxxxx 或现场办理（行政楼 305）",
    "目前学校的标准流程是线上提交 + 线下确认两步",
    "校历上有明确说明，建议查阅官网最新通知",
    "需要班主任签字后交到学生处统一办理",
    "属于辅导员对接事项，请直接联系所在班级辅导员",
]
TEACHER_REPLY_TEMPLATES = [
    "已经为你确认过了，{detail}。如还有问题请回复或来办公室找我。",
    "好的，我刚才查了一下，{detail}。下次有类似问题可以直接来找辅导员。",
    "收到你的问题，{detail}。这块政策最近确实有点变动，按这个说法办就行。",
    "辛苦你的耐心，{detail}。如果按这个流程走还有卡点，随时反馈。",
    "已经帮你协调过教务，{detail}。具体可以查看院系群里转发的通知。",
]
TEACHER_DETAILS = [
    "你按上面 AI 的指引去办即可，遇到问题告诉我具体卡在哪一步",
    "这周五前提交就来得及，材料注意按要求的顺序装订",
    "我把你的情况已经反馈给学院教务，等通知",
    "你的问题我已经登记，下周一开会讨论会带上",
    "请把申请表填好发我邮箱（lingji@sdfmu.edu.cn），我帮你转",
    "已经为你预约了下周三上午 10 点的面谈",
    "可以的，我刚和分管老师沟通过，没问题",
    "稍等下我跟教务再核实下，今天之内回你",
]
KB_TITLES = [
    "学生证补办的标准流程与材料清单",
    "奖学金 / 助学金申请时间窗口与审核标准",
    "宿舍调换办理路径与典型审批周期",
    "毕业论文格式规范与提交节点",
    "选课系统使用指南：抢课 / 退课 / 冲突解决",
    "学费缴纳方式与分期申请条件",
    "心理咨询中心预约方式与服务范围",
    "校医院常见问题转诊指南",
    "体测不及格补测的申请与备考建议",
    "校园卡挂失补办流程",
    "辅修 / 双学位申请要点",
    "出国交流项目流程与常见 FAQ",
    "校园网账号与无线接入说明",
    "新生入学手册：报到流程与必备物品",
    "党课 / 团课报名与考核要点",
    "实习证明 / 实习考核办理方法",
    "请假 / 销假流程及销假凭证",
    "课表冲突处理流程",
    "教学楼开放时间与自习管理",
    "学院公众号订阅与重要通知获取渠道",
    "校历常见时间节点速查",
    "毕业生档案 / 户口迁移办理",
    "校内打印复印自助服务点位",
    "校友卡办理 / 续期",
    "校园安全与一键报警使用指南",
]

KB_CONTENT_TEMPLATE = (
    "适用对象：{audience}\n"
    "办理路径：{path}\n"
    "所需材料：{materials}\n"
    "办理时间：{timing}\n"
    "联系电话：{phone}\n"
    "备注：{notes}"
)


def _gen_kb_content() -> str:
    return KB_CONTENT_TEMPLATE.format(
        audience=random.choice(["全体本科生", "全体研究生", "在校学生（含留学生）", "应届毕业生"]),
        path=random.choice([
            "登录教务系统 → 学生服务 → 提交申请 → 等待辅导员审核",
            "下载申请表 → 班主任签字 → 院系盖章 → 学生处归档",
            "线上提交申请 → 院办初审 → 学生处终审 → 微信通知",
        ]),
        materials=random.choice([
            "申请表 1 份、身份证复印件 1 份、学生证复印件 1 份",
            "在线表单 + 证明材料扫描件（pdf 格式，单份小于 10MB）",
            "纸质申请表 + 关联材料原件（现场核验后退还）",
        ]),
        timing=random.choice([
            "工作日 09:00-11:30 / 14:00-17:00（节假日及周末暂停）",
            "每月 1 日-10 日集中受理，其他时间可在线提交但响应较慢",
            "随到随办，平均 3 个工作日内反馈",
        ]),
        phone=fake.phone_number(),
        notes=random.choice([
            "若材料不齐全将退回补充，请按清单准备",
            "节假日前后受理量较大，请提前预约",
            "审批结果将通过校园短信和邮箱通知，请保持联系方式畅通",
            "存在异议可向学院申诉，详见院系公告",
        ]),
    )


def _gen_question(college_name: str = "") -> tuple[str, str]:
    """生成 (title, full_text)"""
    topic, detail = random.choice(TOPICS)
    body = random.choice(QUESTION_TEMPLATES).format(topic=topic, detail=detail)
    # title 取问题前 40 字；body 保留完整文本
    title = topic
    return title, body


def _gen_ai_reply(college_name: str = "学院") -> str:
    return random.choice(AI_REPLY_TEMPLATES).format(
        college_name=college_name or "学院",
        advice=random.choice(AI_ADVICE),
    )


def _gen_teacher_reply() -> str:
    return random.choice(TEACHER_REPLY_TEMPLATES).format(
        detail=random.choice(TEACHER_DETAILS),
    )


# ─── conv mode ────────────────────────────────────────────────────
def mode_conv(args: argparse.Namespace) -> None:
    _enforce_non_prod(args.gateway_url)

    if not args.confirm:
        sys.exit(
            "⚠️  dry-run：要真写入请加 --confirm\n"
            f"   计划：在 {args.gateway_url} 创建 {args.count} 条 conversation\n"
            f"   学生池：args.students={args.students or '(全部活跃学生)'}\n"
            "   状态分布：约 15% pending_teacher / 25% teacher_serving / 40% resolved / 20% ai_serving"
        )

    # 1. admin 登录拿 student 列表
    print(f"[1/4] admin 登录 {args.gateway_url} …")
    admin = Client.login(args.gateway_url, args.admin_staff_id, args.admin_password)
    print(f"      ✓ admin user_id={admin.user_id}")

    # 2. fetch students（API page size 上限 100，需要时分页拼接）
    print("[2/4] 拉取学生池 …")
    student_items: list[dict] = []
    for page in range(1, 10):  # 上限 900 学生
        sr = admin.get("/api/admin/users", {"page": page, "size": 100, "role": "student"})
        if sr.status_code != 200:
            sys.exit(f"admin /api/admin/users 失败：{sr.status_code} {sr.text[:200]}")
        items = sr.json().get("items") or []
        if not items:
            break
        student_items.extend(items)
        if len(items) < 100:
            break
    # 排除 pilot:xxx 测试账号
    student_items = [s for s in student_items if not (s.get("staff_id") or "").lower().startswith("pilot:")]
    if args.students:
        wanted = set(args.students.split(","))
        student_items = [s for s in student_items if s["staff_id"] in wanted]
    if not student_items:
        sys.exit("学生池为空，无法 seed。")
    print(f"      ✓ 学生池 size={len(student_items)} (排除 pilot:* 测试号)")

    # 3. teacher 登录（accept / resolve 用）
    print("[3/4] teacher 登录 …")
    teacher = Client.login(args.gateway_url, args.teacher_staff_id, args.teacher_password)
    print(f"      ✓ teacher user_id={teacher.user_id}")

    # 4. 灌 N 条 conversation
    print(f"[4/4] 开始生成 {args.count} 条 conversation …")
    manifest = []
    stu_token_cache: dict[str, Client] = {}
    status_targets = {
        "ai_serving": int(args.count * 0.20),
        "pending_teacher": int(args.count * 0.15),
        "teacher_serving": int(args.count * 0.25),
        "resolved": args.count - int(args.count * 0.20) - int(args.count * 0.15) - int(args.count * 0.25),
    }
    status_queue = (
        ["ai_serving"] * status_targets["ai_serving"]
        + ["pending_teacher"] * status_targets["pending_teacher"]
        + ["teacher_serving"] * status_targets["teacher_serving"]
        + ["resolved"] * status_targets["resolved"]
    )
    random.shuffle(status_queue)

    for i, target_status in enumerate(status_queue):
        student = random.choice(student_items)
        college_name = student.get("college_name") or "学院"
        title_topic, full_question = _gen_question(college_name)

        # cache student tokens to avoid relogin spam
        sid = student["staff_id"]
        if sid not in stu_token_cache:
            try:
                stu_token_cache[sid] = Client.login(args.gateway_url, sid, sid)  # password == staff_id 约定
            except Exception as e:
                print(f"      [skip] {sid} login 失败：{e}")
                continue
        stu = stu_token_cache[sid]

        # create conv
        title = f"{DEMO_MARKER} {title_topic}"
        r = stu.post("/api/conversations", {"title": title})
        if r.status_code not in (200, 201):
            print(f"      [skip] {sid} create conv 失败：{r.status_code} {r.text[:160]}")
            continue
        conv_id = r.json()["id"]
        manifest.append({"conv_id": conv_id, "student_staff_id": sid, "target_status": target_status})

        # post initial student message
        stu.post(f"/api/conversations/{conv_id}/messages",
                 {"content": f"{DEMO_MARKER} {full_question}"})

        # 用 admin 直接推 AI/teacher 假消息？不行，gateway 走 student/teacher 路径。
        # 改用 teacher.send_message 模拟教师回复；AI 回复通过让教师身份说"AI 答复"是不对的。
        # 简化：跳过 AI 拟态，直接 escalate → accept → 让 teacher 回复 → 视目标 resolve

        if target_status == "ai_serving":
            # 留在 ai_serving；不 escalate
            pass
        else:
            # escalate to pending_teacher
            esc = stu.post(f"/api/conversations/{conv_id}/escalate")
            if esc.status_code not in (200, 201):
                print(f"      [warn] conv {conv_id} escalate 失败：{esc.status_code}")
                continue
            if target_status == "pending_teacher":
                pass  # stop here
            else:
                # teacher accept
                acc = teacher.post(f"/api/conversations/{conv_id}/accept")
                if acc.status_code not in (200, 201):
                    print(f"      [warn] conv {conv_id} accept 失败：{acc.status_code}")
                    continue
                # teacher reply
                teacher.post(f"/api/conversations/{conv_id}/messages",
                             {"content": f"{DEMO_MARKER} {_gen_teacher_reply()}"})
                if target_status == "resolved":
                    rv = teacher.post(f"/api/conversations/{conv_id}/resolve")
                    if rv.status_code not in (200, 201):
                        print(f"      [warn] conv {conv_id} resolve 失败：{rv.status_code}")

        if (i + 1) % 10 == 0:
            print(f"      进度 {i + 1}/{args.count}")
        time.sleep(0.03)  # 轻微限流

    print("─" * 60)
    print(f"✓ 已 seed {len(manifest)} 条 conversation")
    by_status: dict[str, int] = {}
    for m in manifest:
        by_status[m["target_status"]] = by_status.get(m["target_status"], 0) + 1
    for k, v in by_status.items():
        print(f"   {k}: {v}")
    print(f"   marker: 所有 title / message 内容均以 '{DEMO_MARKER}' 开头")
    print(f"   cleanup: python {sys.argv[0]} cleanup-sql | ssh ... 'docker exec -i yx_postgres psql ...'")


# ─── kb-sql mode (emit SQL) ───────────────────────────────────────
def _sql_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def mode_kb_sql(args: argparse.Namespace) -> None:
    # kb-sql 只是输出 SQL 不直接连库，因此 prod guard 仅校验 APP_ENV
    app_env = (os.getenv("APP_ENV") or "dev").lower()
    if app_env in {"prod", "production"}:
        sys.exit("❌ APP_ENV=prod，拒绝生成 kb-sql。")

    print("-- ============================================================")
    print(f"-- 医小管 seed-demo-data.py kb-sql · {args.kb_count} entries")
    print(f"-- generated at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"-- marker prefix: {DEMO_MARKER}")
    print("-- 用法：python seed-demo-data.py kb-sql --kb-count N | \\")
    print("--      ssh easten@192.168.100.165 'docker exec -i yx_postgres psql -U yxg -d yixiaoguan_v2'")
    print("-- ============================================================")
    print("BEGIN;")
    print()

    # 1. unanswered_questions：N/3 条（教师"高频待补"页面可看到）
    uq_count = max(args.kb_count // 3, 5)
    print(f"-- {uq_count} unanswered_questions（教师『高频待补』展示）")
    for i in range(uq_count):
        topic, _detail = random.choice(TOPICS)
        qtext = f"{DEMO_MARKER} {topic}"
        qhash = f"demo_hash_{i:04d}_{int(time.time())}"
        hit_count = random.randint(2, 47)
        # college_id NULL = 全校；mix 一些挂到具体学院
        college_clause = "NULL" if random.random() < 0.4 else str(random.randint(1, 21))
        print(
            "INSERT INTO unanswered_questions "
            "(question_text, question_hash, hit_count, sample_conv_ids, college_id, is_resolved) "
            f"VALUES ({_sql_quote(qtext)}, {_sql_quote(qhash)}, {hit_count}, "
            f"ARRAY[]::integer[], {college_clause}, false);"
        )

    print()
    # 2. kb_suggestions：args.kb_count 条
    # 分布：5 global pending（admin 待审）+ 8 class approved + 12 college approved
    # 提交人 = anjing (user_id 通常 6，安全起见用 staff_id='anjing' 子查询)
    pending_n = max(args.kb_count // 5, 3)
    approved_n = args.kb_count - pending_n
    print(f"-- {pending_n} kb_suggestions(pending, global) — 管理员审核列表展示")
    print(f"-- {approved_n} kb_suggestions(approved, class/college) — 已发布")
    for i in range(args.kb_count):
        title = f"{DEMO_MARKER} {random.choice(KB_TITLES)}"
        content = _gen_kb_content().replace("'", "''")
        raw_content = content
        repr_q = random.choice(TOPICS)[0]
        qhash = f"demo_kb_hash_{i:04d}_{int(time.time())}"
        if i < pending_n:
            scope = "global"
            scope_value = "NULL"
            status = "pending"
            college_id = "NULL"
            reviewed_at = "NULL"
            published_at = "NULL"
        else:
            scope = random.choice(["class", "college"])
            scope_value = str(random.randint(1, 21)) if scope == "college" else str(random.randint(1, 50))
            status = "approved"
            college_id = scope_value if scope == "college" else "NULL"
            reviewed_at = "NOW()"
            published_at = "NOW()"
        # submitted_by: anjing (teacher) — 用子查询安全
        # 注意：枚举字段必须用枚举字面量（PG 会 cast）
        print(
            "INSERT INTO kb_suggestions "
            "(title, content, raw_content, source, source_url, college_id, scope, scope_value, "
            "representative_query, question_hash, status, submitted_by, reviewed_by, "
            "reject_reason, dify_document_id, created_at, published_at, reviewed_at) "
            f"VALUES ({_sql_quote(title)}, {_sql_quote(content)}, {_sql_quote(raw_content)}, "
            f"'teacher_input', NULL, {college_id}, {_sql_quote(scope)}::knowledgescope, {scope_value}, "
            f"{_sql_quote(repr_q)}, {_sql_quote(qhash)}, "
            f"{_sql_quote(status)}::suggestionstatus, "
            f"(SELECT id FROM users WHERE staff_id='anjing' LIMIT 1), "
            f"{'NULL' if status == 'pending' else '(SELECT id FROM users WHERE staff_id=' + chr(39) + 'A001' + chr(39) + ' LIMIT 1)'}, "
            f"NULL, NULL, NOW(), {published_at}, {reviewed_at});"
        )

    print()
    print("-- 验证")
    print(f"SELECT '[demo] kb_suggestions seeded: ' || count(*) FROM kb_suggestions WHERE title LIKE '{DEMO_MARKER}%';")
    print(f"SELECT '[demo] unanswered_questions seeded: ' || count(*) FROM unanswered_questions WHERE question_text LIKE '{DEMO_MARKER}%';")
    print("COMMIT;")


# ─── cleanup-sql mode ─────────────────────────────────────────────
def mode_cleanup_sql(_args: argparse.Namespace) -> None:
    print("-- ============================================================")
    print(f"-- 医小管 seed-demo-data.py cleanup-sql")
    print(f"-- generated at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"-- 删除所有 title / question_text / content 以 '{DEMO_MARKER}' 开头的行")
    print("-- 顺序：message → conversation → kb_suggestion → unanswered_question")
    print("-- ============================================================")
    print("BEGIN;")
    print()
    # 1. delete messages of demo convs
    print("-- 1. 删除所有 demo 标记 conversation 的 messages（FK 限制需先删子表）")
    print(f"""DELETE FROM messages
WHERE conversation_id IN (
  SELECT id FROM conversations WHERE title LIKE '{DEMO_MARKER}%'
);""")
    print()
    # 2. delete demo convs
    print("-- 2. 删除 demo conversations")
    print(f"""DELETE FROM conversations WHERE title LIKE '{DEMO_MARKER}%';""")
    print()
    # 3. delete kb_suggestions where title prefixed
    # unanswered_questions.kb_suggestion_id FK → kb_suggestions.id，先 null 化引用
    print("-- 3. 先解除 unanswered_questions 对 demo kb_suggestions 的 FK 引用")
    print(f"""UPDATE unanswered_questions SET kb_suggestion_id = NULL
WHERE kb_suggestion_id IN (
  SELECT id FROM kb_suggestions WHERE title LIKE '{DEMO_MARKER}%'
);""")
    print()
    print("-- 4. 删除 demo kb_suggestions")
    print(f"""DELETE FROM kb_suggestions WHERE title LIKE '{DEMO_MARKER}%';""")
    print()
    print("-- 5. 删除 demo unanswered_questions")
    print(f"""DELETE FROM unanswered_questions WHERE question_text LIKE '{DEMO_MARKER}%';""")
    print()
    print("-- 验证")
    print(f"""SELECT 'remaining demo conv: ' || count(*) FROM conversations WHERE title LIKE '{DEMO_MARKER}%';""")
    print(f"""SELECT 'remaining demo kb: ' || count(*) FROM kb_suggestions WHERE title LIKE '{DEMO_MARKER}%';""")
    print(f"""SELECT 'remaining demo uq: ' || count(*) FROM unanswered_questions WHERE question_text LIKE '{DEMO_MARKER}%';""")
    print("COMMIT;")


# ─── list-sql mode ────────────────────────────────────────────────
def mode_list_sql(_args: argparse.Namespace) -> None:
    print("-- 列出当前 demo 标记内容（只读）")
    print(f"""SELECT 'conversations marked demo: ' || count(*) FROM conversations WHERE title LIKE '{DEMO_MARKER}%';""")
    print(f"""SELECT 'kb_suggestions marked demo: ' || count(*) FROM kb_suggestions WHERE title LIKE '{DEMO_MARKER}%';""")
    print(f"""SELECT 'unanswered_questions marked demo: ' || count(*) FROM unanswered_questions WHERE question_text LIKE '{DEMO_MARKER}%';""")
    print(f"""SELECT id, status, title FROM conversations WHERE title LIKE '{DEMO_MARKER}%' ORDER BY id DESC LIMIT 30;""")
    print(f"""SELECT id, status, scope, title FROM kb_suggestions WHERE title LIKE '{DEMO_MARKER}%' ORDER BY id DESC LIMIT 30;""")


# ─── main ─────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(description="医小管 demo data seed (dev/staging only)")
    sub = p.add_subparsers(dest="mode", required=True)

    p_conv = sub.add_parser("conv", help="HTTP API 创建 conversation + messages")
    p_conv.add_argument("--count", type=int, default=60)
    p_conv.add_argument("--gateway-url", default=os.getenv("GATEWAY_URL") or "http://192.168.100.165:8100")
    p_conv.add_argument("--admin-staff-id", default=os.getenv("ADMIN_STAFF_ID") or "A001")
    p_conv.add_argument("--admin-password", default=os.getenv("ADMIN_PASSWORD") or "admin123")
    p_conv.add_argument("--teacher-staff-id", default=os.getenv("TEACHER_STAFF_ID") or "anjing")
    p_conv.add_argument("--teacher-password", default=os.getenv("TEACHER_PASSWORD") or "Anjing@yxg2026")
    p_conv.add_argument("--students", help="可选：逗号分隔的 staff_id 白名单（默认所有活跃学生）")
    p_conv.add_argument("--confirm", action="store_true", help="确认写入；不带本 flag 则 dry-run")
    p_conv.set_defaults(func=mode_conv)

    p_kb = sub.add_parser("kb-sql", help="生成 KB / unanswered_questions 的 INSERT SQL（stdout）")
    p_kb.add_argument("--kb-count", type=int, default=25)
    p_kb.set_defaults(func=mode_kb_sql)

    p_cl = sub.add_parser("cleanup-sql", help="生成清理 SQL（stdout）")
    p_cl.set_defaults(func=mode_cleanup_sql)

    p_ls = sub.add_parser("list-sql", help="生成只读统计 SQL（stdout）")
    p_ls.set_defaults(func=mode_list_sql)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
