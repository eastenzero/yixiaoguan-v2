# 内测前 sprint 进度 — 2026-04-28 17:30 ~ 18:45 CST

## 今晚已完成（5/11 项 = 45%）

| Kimi # | 项 | 落地 |
|---|---|---|
| 🔴 #1 | 学生端 H5 没构建 | `apps/student-app/dist/build/h5/` 全新 (440K)，含 P0-2 sticky CTA |
| 🔴 #11 | 教师端 H5 14 天没更新 | `apps/teacher-app/dist/build/h5/` 全新 (408K)，含 P1-1 + Sprint 2.5/2.6 |
| 🟡 #7 | JWT secret 硬编码 fallback | `config.py` 删默认值 + 启动校验 + 弱密钥黑名单 |
| 🟡 #8 | JWT TTL 72h 过长 | 24h |
| ⚠️ +1 | 165 .env 实际用着默认弱密钥 | 轮换为 64 字符 base64url 强随机；旧 .env 备份保留至 `services/gateway/.env.bak.20260428-183004` |
| ⚠️ +1 | 主仓根目录有学生 PII 文件 | `.gitignore` 增加 `/工作簿.xlsx /填空.docx /文档/ /358*Smn2fN.xlsx ...` 全部隔离；`.env.bak.*` 也已加入忽略 |

## 主仓 master 新增 commits（已 push 到 GitHub）

```
7b45397 chore(gitignore): protect student PII files and .env backups
d4fd3ef fix(security): require strong JWT_SECRET, reject weak placeholders, shorten TTL to 24h
90f77bf docs(audit): add Kimi pre-pilot security and infra audit (2026-04-28)
9abd7ea docs(dev): add codex-dispatch-guide for Cascade-Codex async workflow
```

## 165 当前部署状态

- 代码：`5cca394` → `d4fd3ef`（已 git pull + reset）
- Gateway：PID 3089949，新强密钥跑起来，`GET /api/conversations` 用新 token = 200
- mutagen 同步：主仓 ↔ 165 双向（`yixiaoguan-v2` session）
- 现存学生：3（张小洋/李小辉/张小泰）+ 教师 1（梁淑芬）+ 管理员 1
- 现存班级：临床 2024-1 / 护理 2024-1 / 放射 2024-1（全部 college_id 不同）

## 明天需做（6 项 + 用户加 1 项 = 7 项）

### 阻塞项（必须）

**A. xlsx 批量导入（用户已交付 `/工作簿.xlsx`）— 信息全齐，可直接派单**
- 名单：48 学生（row 1: 余文惠 4124150001 + row 2-48: 47 人 4125150001-4125150047）
- ⚠️ Row 37 学号 `4125750036` 疑似 typo（应为 `4125150036`），已确认按 typo 处理
- **学院**：医药管理学院（如不存在则新建）
- **专业**：公共事业管理
- **班级**：48 人都算同班 → 命名 `公共事业管理 2025-1 班`（沿用现有 `XX 2024-1 班` 风格；user 说"随便填"）
- 学生：staff_id = 学号、初始密码 = bcrypt(学号)、role=student、college_id = 医药管理学院、class_id = 公共事业管理 2025-1 班
- 辅导员"安静"：staff_id=anjing、初始密码 bcrypt(`Anjing@yxg2026`)、role=teacher、college_id = 医药管理学院、class_id = 公共事业管理 2025-1 班
- 同班同学互登风险：在班级通知里告知首次登录后立刻改密
- 验收：`select count(*) from users where role='student'` = 51（3 + 48）；辅导员 anjing 用 `Anjing@yxg2026` 能登录 + 收到该班学生 escalate 队列

**B. DB 备份 cron** (Kimi #3)
- 写 `/home/easten/dev/yixiaoguan-v2/scripts/pg-backup.sh`：`pg_dump yixiaoguan_v2 | gzip > /home/easten/backups/yxgv2-$(date +%Y%m%d).sql.gz`，保留 7 天滚动
- crontab 每日凌晨 2:00 执行
- 验收：`/home/easten/backups/` 有今日 dump 文件

**C. Gateway systemd unit** (Kimi #4)
- `/etc/systemd/system/yixiaoguan-gateway.service`：User=easten，WorkingDirectory，EnvironmentFile=.env，Restart=on-failure
- 启用：`systemctl enable + start`
- 验收：`kill -9 $(pgrep -f uvicorn)` 后 5s 内自动恢复

### 强烈建议（应做）

**D. 登录 rate limit** (Kimi #5)
- 在 `services/gateway/app/routers/auth.py` `/api/auth/login` 加 IP 级限流：5 次错误密码/分钟 → 429
- 用 redis 计数（已有 redis_url）
- 验收：连续 6 次错误密码，第 6 次 = 429

**E. ufw + 关闭 5432/6379 公网暴露** (Kimi #6)
- `sudo ufw allow 22, 80, 443; sudo ufw deny 5432, 6379, 8100; sudo ufw enable`
- ⚠️ 8100 不再暴露公网，必须先有 nginx 反代到 8100（项 F）才能 deny 8100
- 验收：从外网 telnet 5432 fail；nginx 转发 /api/ → 127.0.0.1:8100 OK

**F. nginx 反向代理 + 静态 H5 + HTTPS** (Kimi #10)
- nginx config：
  - `location /api/` → `proxy_pass http://127.0.0.1:8100/`
  - `location /` → `root /home/easten/dev/yixiaoguan-v2/apps/student-app/dist/build/h5/`
  - `location /teacher/` → `alias /home/easten/dev/yixiaoguan-v2/apps/teacher-app/dist/build/h5/`
  - HTTPS：自签证书 + redirect 80 → 443（如时间紧）；或 LE
- 验收：`curl https://192.168.100.165/` 返回 student-app HTML；`curl https://192.168.100.165/api/health` 通

### 用户加项

**G. 主仓根目录清理**
- 现有 root 文件：`bailian.txt mutagen.yml mutagen.yml.lock README.md s1-...md s2-...md s3-...md test_login.py ws_test.py gateway.log migrate_result.csv 工作簿.xlsx 填空.docx 358*Smn2fN.xlsx`
- 策略：
  - 保留：`README.md mutagen.yml mutagen.yml.lock .gitignore .windsurfrules`
  - 移到 `.archive/2026-04/`：`s1-...md s2-...md s3-...md test_login.py ws_test.py bailian.txt`
  - 删除：`gateway.log migrate_result.csv 358*Smn2fN.xlsx`（已 ignore，重复无价值）
  - 不动：`工作簿.xlsx 填空.docx 文档/`（PII，user 自己决定何时删）
- 验收：`git status --short` 无 untracked 在 root，root 里只剩 README+config+目录

## 跳过的今晚选项

- 起 python http.server 让用户用浏览器验证 P1-1/P0-2 H5 — 不紧迫
- 加"首次登录强制改密"功能 — 用户选 B 不做
- nginx 静态 location — 移到明天 sprint F

## 关键参考

- Kimi 完整审计：`.tasks/kimi-pilot-audit-report.md`（253 行）
- codex 派单流程：`docs/dev/codex-dispatch-guide.md`
- 用户最终方案：B 选项（辅导员密码 `Anjing@yxg2026`、学生学号=密码、不加强制改密、Row 37 typo 修正、加根目录清理）
- 165 ssh：`easten@192.168.100.165`，gateway in `/home/easten/dev/yixiaoguan-v2/services/gateway`
