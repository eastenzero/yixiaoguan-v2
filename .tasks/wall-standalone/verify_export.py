#!/usr/bin/env python3
# 跑 wall_export.py --dry, 提取关键字段做摘要
import json, subprocess, sys

cp = subprocess.run(
    ["python3", "/home/easten/dev/yixiaoguan-v2/scripts/wall_export.py", "--dry"],
    capture_output=True, text=True,
)
if cp.returncode != 0:
    sys.stderr.write(cp.stderr)
    sys.exit(cp.returncode)

d = json.loads(cp.stdout)
print(f"generated_at : {d['generated_at']}")
print(f"day_num      : {d['day_num']}")
print(f"kpis         : {d['kpis']}")
print(f"funnel cnts  : {[r['cnt'] for r in d['funnel']]}")
print(f"daily rows   : {len(d['daily'])}")
for r in d["daily"]:
    print(f"  {r['day']}  asked={r['asked']:>3}  answered={r['answered']:>3}  active={r['active']:>3}")
print(f"ticker rows  : {len(d['ticker'])}")
for r in d["ticker"][:6]:
    detail = (r["detail"] or "").replace("\n", " ")[:40]
    college = r["college"] or "-"
    print(f"  [{r['t']}] {r['evt']:<8}  role={r['role']}  college={college}  detail={detail or '-'}")
print(f"error        : {d.get('error')}")
print(f"elapsed_ms   : {d.get('elapsed_ms')}")
