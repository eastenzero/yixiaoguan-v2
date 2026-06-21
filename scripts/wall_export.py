#!/usr/bin/env python3
"""
医小管 · 内测大屏 · 数据导出
================================================================

用途  : 从 postgres (yixiaoguan_v2.public) 的 v_* view 读取 4 块数据,
        生成大屏前端消费的 JSON 快照, 原子写到
        /var/www/yixiaoguan/wall/data.json

调度  : systemd timer, 每 5 分钟一次 (见 yxg-wall-export.timer)

运行  : python3 wall_export.py
        python3 wall_export.py --out /tmp/wall.json   (自定义输出)
        python3 wall_export.py --dry                  (只打印, 不写文件)

依赖  : psycopg[binary] >= 3.1  (apt: python3-psycopg or pip install psycopg[binary])

设计原则:
- 任何单个查询报错 → 该块输出降级 (空 list / 0 数字), 不让全局失败
- 全局报错 → 仍输出合法 JSON (含 error 字段), 前端不白屏
- 原子写: 先写 data.json.tmp, rename 成 data.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import traceback
from datetime import date, datetime, timezone, timedelta

# psycopg 3 (新) 或 psycopg2 (旧) 都接受
try:
    import psycopg  # type: ignore
    _USE_V3 = True
except ImportError:  # pragma: no cover
    try:
        import psycopg2 as psycopg  # type: ignore
        _USE_V3 = False
    except ImportError:
        sys.stderr.write(
            "ERROR: 缺少 psycopg 依赖。请先装:\n"
            "  sudo apt install python3-psycopg  # ubuntu 22+\n"
            "或:\n"
            "  pip3 install 'psycopg[binary]'\n"
        )
        sys.exit(2)


# ──────────────────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────────────────
DB_DSN = {
    "host":     os.environ.get("YXG_DB_HOST", "127.0.0.1"),
    "port":     int(os.environ.get("YXG_DB_PORT", "5432")),
    "dbname":   os.environ.get("YXG_DB_NAME", "yixiaoguan_v2"),
    "user":     os.environ.get("YXG_DB_USER", "ro_bi"),
    "password": os.environ.get(
        "YXG_DB_PASS",
        "f0263944224d4b2470a57bb788d87f4a",
    ),
    "connect_timeout": 5,
}

# 内测启动日 (day_num 从这天 = 第 1 天算起)
PILOT_START_DATE = date(2026, 5, 8)

# 默认输出路径
DEFAULT_OUT = "/var/www/yixiaoguan/wall/data.json"

# 北京时区 (服务器可能是 UTC)
BEIJING_TZ = timezone(timedelta(hours=8))


# ──────────────────────────────────────────────────────────
# SQL
# ──────────────────────────────────────────────────────────

# 6 大 KPI (active=今日, 其他=累计)
SQL_KPIS = """
SELECT
  COALESCE((SELECT SUM(active_users) FROM v_kpi_daily WHERE day = CURRENT_DATE), 0)          AS active,
  COALESCE((SELECT SUM(chat_sends)   FROM v_kpi_daily), 0)                                   AS questions,
  COALESCE((SELECT SUM(chat_ok)      FROM v_kpi_daily), 0)                                   AS answered,
  CASE WHEN COALESCE((SELECT SUM(chat_sends) FROM v_kpi_daily), 0) > 0
       THEN ROUND(100.0 * (SELECT SUM(chat_ok) FROM v_kpi_daily)::numeric
                        / NULLIF((SELECT SUM(chat_sends) FROM v_kpi_daily), 0), 0)
       ELSE 0 END                                                                            AS ai_rate,
  COALESCE((SELECT SUM(card_shown)   FROM v_kpi_daily), 0)                                   AS blind,
  COALESCE((SELECT SUM(card_submitted) + SUM(feedback_submitted) FROM v_kpi_daily), 0)       AS feedback;
"""

# 用户漏斗 (内测期仅 pilot)
SQL_FUNNEL = """
SELECT
  SUM(s1_started::int)        AS s1,
  SUM(s2_browsed::int)        AS s2,
  SUM(s3_asked::int)          AS s3,
  SUM(s4_got_answer::int)     AS s4,
  SUM(s5_card_shown::int)     AS s5,
  SUM(s6_gave_feedback::int)  AS s6
FROM v_funnel_user
WHERE user_type = 'pilot';
"""

# 日级趋势 (最近 14 天)
SQL_DAILY = """
SELECT
  day::text                                 AS day,
  COALESCE(SUM(chat_sends), 0)::int         AS asked,
  COALESCE(SUM(chat_ok), 0)::int            AS answered,
  COALESCE(SUM(active_users), 0)::int       AS active
FROM v_kpi_daily
WHERE day >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY day
ORDER BY day;
"""

# 最近 20 条事件 (排除 page_view 淹没)
# NOTE: client_ts 存的是 UTC (学生手机时钟值), created_at 是服务器北京时间 (接收时)
# 大屏展示用 created_at 最直观 (服务器视角)
SQL_TICKER = """
SELECT
  to_char(created_at, 'HH24:MI')                                                                      AS t,
  event_name,
  CASE event_name
    WHEN 'chat_send'              THEN '提问'
    WHEN 'chat_response_ok'       THEN 'AI 解答'
    WHEN 'service_card_click'     THEN '服务跳转'
    WHEN 'quick_question_click'   THEN '快捷问'
    WHEN 'kb_doc_clicked'         THEN '点开文档'
    WHEN 'unanswered_card_shown'  THEN '盲区出现'
    WHEN 'unanswered_user_filled' THEN '盲区反馈'
    WHEN 'unanswered_card_dismissed' THEN '盲区忽略'
    WHEN 'feedback_form_open'     THEN '打开反馈'
    WHEN 'feedback_form_submit'   THEN '提交反馈'
    WHEN 'app_start'              THEN '启动 App'
    ELSE event_name
  END                                                                                                 AS evt,
  COALESCE(
    NULLIF(props->>'card', ''),
    NULLIF(props->>'label', ''),
    NULLIF(props->>'source_title', ''),
    NULLIF(props->>'path', ''),
    ''
  )                                                                                                   AS detail,
  COALESCE(college_name, '')                                                                          AS college,
  COALESCE(props->>'role', user_type)                                                                 AS role
FROM v_events_enriched
WHERE event_name <> 'page_view'
ORDER BY created_at DESC
LIMIT 20;
"""


# ──────────────────────────────────────────────────────────
# 查询执行 (带独立错误处理)
# ──────────────────────────────────────────────────────────

def _fetchone(cur, sql: str) -> dict | None:
    cur.execute(sql)
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def _fetchall(cur, sql: str) -> list[dict]:
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def query_kpis(cur) -> dict:
    try:
        row = _fetchone(cur, SQL_KPIS) or {}
        return {k: int(v or 0) for k, v in row.items()}
    except Exception as e:
        sys.stderr.write(f"[kpis] failed: {e}\n")
        return {
            "active": 0, "questions": 0, "answered": 0,
            "ai_rate": 0, "blind": 0, "feedback": 0,
        }


def query_funnel(cur) -> list[dict]:
    labels = [
        (1, "启动 App"),
        (2, "浏览页面"),
        (3, "提出问题"),
        (4, "收到回复"),
        (5, "触达盲区"),
        (6, "留下反馈"),
    ]
    try:
        row = _fetchone(cur, SQL_FUNNEL) or {}
        counts = [int(row.get(f"s{i}") or 0) for i in range(1, 7)]
        return [
            {"ord": ord_, "step": step, "cnt": counts[ord_ - 1]}
            for ord_, step in labels
        ]
    except Exception as e:
        sys.stderr.write(f"[funnel] failed: {e}\n")
        return [
            {"ord": ord_, "step": step, "cnt": 0}
            for ord_, step in labels
        ]


def query_daily(cur) -> list[dict]:
    try:
        rows = _fetchall(cur, SQL_DAILY)
        return [
            {
                "day":      r.get("day"),
                "asked":    int(r.get("asked") or 0),
                "answered": int(r.get("answered") or 0),
                "active":   int(r.get("active") or 0),
            }
            for r in rows
        ]
    except Exception as e:
        sys.stderr.write(f"[daily] failed: {e}\n")
        return []


def query_ticker(cur) -> list[dict]:
    try:
        rows = _fetchall(cur, SQL_TICKER)
        role_cn = {"student": "学生", "teacher": "教师", "pilot": "内测"}
        out = []
        for r in rows:
            role_raw = (r.get("role") or "").strip()
            out.append({
                "t":       r.get("t") or "",
                "evt":     r.get("evt") or "",
                "detail":  (r.get("detail") or "")[:80],
                "college": r.get("college") or "",
                "role":    role_cn.get(role_raw, role_raw or "—"),
            })
        return out
    except Exception as e:
        sys.stderr.write(f"[ticker] failed: {e}\n")
        return []


# ──────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────

def compute_day_num() -> int:
    today = datetime.now(BEIJING_TZ).date()
    return max(1, (today - PILOT_START_DATE).days + 1)


def build_snapshot() -> dict:
    snapshot: dict = {
        "generated_at": datetime.now(BEIJING_TZ).isoformat(timespec="seconds"),
        "day_num":      compute_day_num(),
        "kpis":         {"active": 0, "questions": 0, "answered": 0, "ai_rate": 0, "blind": 0, "feedback": 0},
        "funnel":       [],
        "daily":        [],
        "ticker":       [],
        "error":        None,
    }

    try:
        if _USE_V3:
            conn_str = (
                f"host={DB_DSN['host']} port={DB_DSN['port']} "
                f"dbname={DB_DSN['dbname']} user={DB_DSN['user']} "
                f"password={DB_DSN['password']} connect_timeout={DB_DSN['connect_timeout']}"
            )
            conn = psycopg.connect(conn_str)
        else:  # psycopg2 回退
            conn = psycopg.connect(
                host=DB_DSN["host"], port=DB_DSN["port"],
                dbname=DB_DSN["dbname"], user=DB_DSN["user"],
                password=DB_DSN["password"],
                connect_timeout=DB_DSN["connect_timeout"],
            )
    except Exception as e:
        snapshot["error"] = f"connect_failed: {e}"
        return snapshot

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = 5000;")
                snapshot["kpis"]   = query_kpis(cur)
                snapshot["funnel"] = query_funnel(cur)
                snapshot["daily"]  = query_daily(cur)
                snapshot["ticker"] = query_ticker(cur)
    except Exception as e:
        snapshot["error"] = f"query_failed: {e}\n{traceback.format_exc(limit=2)}"
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return snapshot


def atomic_write(path: str, data: dict) -> None:
    """原子写: tmp → rename, 避免前端 fetch 到半写文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=os.path.dirname(path), prefix=".data.", suffix=".json.tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o644)
        except Exception:
            pass
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="医小管 大屏 数据导出")
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"输出文件 (默认 {DEFAULT_OUT})")
    parser.add_argument("--dry", action="store_true", help="只打印到 stdout, 不写文件")
    args = parser.parse_args()

    t0 = time.time()
    snapshot = build_snapshot()
    elapsed_ms = int((time.time() - t0) * 1000)
    snapshot["elapsed_ms"] = elapsed_ms

    if args.dry:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return 0

    try:
        atomic_write(args.out, snapshot)
        status = "ok" if not snapshot.get("error") else f"ok(with-error: {snapshot['error'][:60]})"
        print(
            f"[wall_export] {status} · "
            f"{elapsed_ms}ms · "
            f"kpis.active={snapshot['kpis']['active']} · "
            f"funnel.s1={snapshot['funnel'][0]['cnt'] if snapshot['funnel'] else 0} · "
            f"daily.rows={len(snapshot['daily'])} · "
            f"ticker.rows={len(snapshot['ticker'])} · "
            f"→ {args.out}"
        )
        return 0 if not snapshot.get("error") else 0  # 降级仍 exit 0, systemd 不报 fail
    except Exception as e:
        sys.stderr.write(f"[wall_export] write failed: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
