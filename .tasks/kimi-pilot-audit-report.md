# 内测前审计报告 — 2026-04-28

> 审计范围：数据现状、API 访问控制、认证强度、网络暴露、部署卫生、密钥管理、前端就绪  
> 审计方式：只读命令，未修改任何数据或服务  
> 审计时间：2026-04-28 15:18 CST

---

## 1. 数据现状

| 实体 | 数量 | 备注 |
|---|---|---|
| 学院 (colleges) | 21 | — |
| 班级 (classes) | 3 | 临床2024-1班、护理2024-1班、放射2024-1班 |
| 学生 (student) | **3** | 张小洋(临床)、李小辉(护理)、张小泰(放射) |
| 教师/辅导员 (teacher) | **1** | 梁淑芬(临床与基础医学院) |
| 管理员 (admin) | **1** | 管理员 |
| 会话 (conversations) | 37 | 学生1占35条，学生5占2条 |
| 消息 (messages) | 205 | — |

会话状态分布：
- `ai_serving`: 25
- `teacher_serving`: 4
- `pending_teacher`: 3
- `resolved`: 4
- `closed`: 1

> ⚠️ **关键发现**：当前仅有 **3 名学生、1 名辅导员**。若内测目标为 30~50 名学生 + 1 名辅导员，**数据缺口极大**，需批量导入测试账号。

---

## 2. API 访问控制

### 2.1 会话列表隔离
- **学生 2024010001** (`STU_TOKEN`) 调用 `GET /api/conversations` 返回 **20 条**，全部为 `student_id=1` 的会话，无越权数据。✅

### 2.2 跨学生越权测试（Conv 38、39 属于学生 5 / 放射学院）
| 接口 | 使用学生 Token | HTTP 状态 | 结论 |
|---|---|---|---|
| `GET /api/conversations/38` | 学生1 | **404** | 无法访问 |
| `GET /api/conversations/38/messages` | 学生1 | **404** | 无法访问 |
| `POST /api/conversations/38/mark-read` | 学生1 | **404** | 无法访问 |
| `POST /api/conversations/38/escalate` | 学生1 | **403** | 被拦截 |
| `GET /api/conversations/39` | 学生1 | **404** | 无法访问 |

- 后端通过 `can_access_conversation()` 做权限校验，无权限时统一返回 **404**（隐藏资源存在性，安全最佳实践）。  
- **结论：跨学生越权 → PASS ✅**

### 2.3 跨学院教师越权测试
- 教师 T001（临床学院，college_id=1）访问属于学生 5（放射学院，college_id=10）的会话 38、39：
  - `GET /api/conversations/38` → **404**
  - `GET /api/conversations/39` → **404**
- 教师列表 `GET /api/conversations` 返回 11 条，全部为同一学院（临床）学生。  
- **结论：跨学院教师越权 → PASS ✅**

### 2.4 Admin endpoint 学生越权测试
- 项目中 **不存在独立的 `/api/admin/` 路由**。Admin 权限以 `UserRole.admin` 角色校验嵌入在现有接口中（如 `knowledge.py`、`actions.py`、`announcements.py`）。  
- 直接访问 `/api/admin/users`、`/api/admin/analytics`、`/api/admin/conversations` 均返回 **404**。  
- **结论：无独立 admin 路由可供越权，现有 admin 角色校验在代码层面完成 → PASS ✅**

---

## 3. 认证强度

### 3.1 JWT 配置
| 项 | 值 | 风险 |
|---|---|---|
| 算法 | **HS256** | 标准 |
| TTL | **72 小时** (`jwt_expire_hours=72`) | 偏长，建议缩短至 8~24 小时 |
| Secret 来源 | 从 `.env` 加载，但代码中存在硬编码回退 `jwt_secret: str = "change-me-in-production"` | ⚠️ **若 .env 缺失将使用弱默认密钥** |

> 建议：删除 `config.py` 中的硬编码默认值，强制要求环境变量。

### 3.2 密码哈希
- 使用 **bcrypt** (`passlib.hash.bcrypt`)  
- Cost factor：**12** (`$2b$12$`)  
- 哈希长度：60 字符  
- **结论：强度合格 ✅**

### 3.3 默认密码风险
对 3 名现有学生测试 `password = staff_id` 登录：
| staff_id | 结果 |
|---|---|
| 2024010001 | **200 成功** |
| 2024020001 | **200 成功** |
| 13800000002 | **401 失败** |

- **2/3 用户仍使用默认密码（staff_id）登录**。  
- ⚠️ 批量导入 30~50 名学生时，若沿用默认密码策略，风险将放大。

### 3.4 登录限流
- 对学生 2024010001 在 1 秒内连续发送 **10 次** 错误密码请求：
  - 返回序列：`401 401 401 401 401 401 401 401 401 401`
- **无任何 429 / 封禁 / 延迟响应**。  
- **结论：登录接口无 rate limit → 高风险 🔴**

---

## 4. 网络暴露

### 4.1 端口监听
| 端口 | 服务 | 监听地址 | 风险 |
|---|---|---|---|
| 8100 | Gateway (uvicorn) | **0.0.0.0** | 直接暴露 |
| 5432 | PostgreSQL | **0.0.0.0** | 直接暴露 |
| 6379 | Redis | **0.0.0.0** | 直接暴露 |
| 80 | nginx | 0.0.0.0 | — |
| 3000 | Dify nginx | 0.0.0.0 | — |
| 3443 | Dify nginx (HTTPS?) | 0.0.0.0 | — |
| 5003 | Dify plugin_daemon | 0.0.0.0 | — |
| 8080 | 未知 | 0.0.0.0 | — |

### 4.2 公网可访问性
- 主机外网/内网 IP：`192.168.100.165`（内网段）、`10.77.0.10`（VPN/tun）
- **ufw: inactive**（防火墙完全关闭）
- iptables 未看到针对 8100 的 DROP 规则
- 8100 绑定在 `0.0.0.0`，从 `192.168.100.165:8100` 可直接访问并返回 404
- **结论：Gateway 在局域网内完全裸奔，若 192.168.100.0/24 可路由至公网则存在暴露风险 🔴**

### 4.3 CORS
- 在 `services/gateway/app/main.py` 及所有 `.py` 文件中 **未找到 `CORSMiddleware` 配置**。
- **结论：CORS 未启用**。对于 H5/小程序跨域场景，浏览器请求将被拦截；但这也意味着不存在 `allow_origins = *` 的过度宽松风险。需确认前端部署方式（同域 / 代理）。

### 4.4 SSL/TLS
- `/etc/nginx/sites-enabled/default` 仅监听 **80**，无 443/SSL 配置
- `/etc/letsencrypt/live/` 不存在
- **无 HTTPS 终止层**。Gateway 8100 为裸 HTTP。  
- **结论：无 HTTPS → 强烈建议 🔴**

---

## 5. 部署卫生

### 5.1 进程管理
- Gateway PID: **1731620**
- 启动方式：`bash -c cd ... && setsid nohup uvicorn app.main:app --host 0.0.0.0 --port 8100 > /tmp/gw.log ...`
- Parent PID: 1731618 (bash) → 最终父进程为 **1** (init)
- **结论：nohup 手动启动，非 systemd ❌**

### 5.2 自动重启
- 无 systemd unit，无 `Restart=on-failure`
- 进程 crash 后不会自动恢复
- **结论：无自动重启 → 阻塞风险 🔴**

### 5.3 日志切割
- 日志文件：`/tmp/gw.log`（大小 **7.0K**，93 行）
- **无 logrotate 配置**
- `/tmp` 下的日志在系统重启后可能丢失
- **结论：无日志持久化与切割方案 🔴**

### 5.4 数据库备份
- `/home/easten/backups/`：**不存在**
- `crontab`：**无 `pg_dump` / backup 任务**
- **结论：无自动备份 → 阻塞风险 🔴**

### 5.5 Dify 健康状态
| 容器 | 状态 |
|---|---|
| docker-api-1 | Up 3 days (healthy) |
| docker-web-1 | Up 6 days |
| docker-nginx-1 | Up 6 days |
| docker-redis-1 | Up 6 days (healthy) |
| docker-sandbox-1 | Up 4 days (healthy) |
| docker-worker-1 | Up 3 days |
| docker-worker_beat-1 | Up 6 days |
| docker-plugin_daemon-1 | Up 6 days |
| docker-db_postgres-1 | Up 6 days (healthy) |
| docker-weaviate-1 | Up 6 days |
| docker-ssrf_proxy-1 | Up 6 days |

- Dify 全部容器运行正常 ✅

---

## 6. 密钥管理

### 6.1 .env 是否曾被 commit
- `.gitignore` 已包含 `.env` / `.venv/` / `venv/`
- `git log --all --full-history -- '*.env'`：**无任何提交记录**
- `git ls-files | grep '\.env'`：**无结果**
- **结论：.env 从未进入版本控制 ✅**

### 6.2 .env 文件现状
- 路径：`services/gateway/.env`
- 权限：`-rw-------` (600) — 仅所有者可读 ✅
- Key 数量：**7 个**

### 6.3 API Key 日志泄漏
- 搜索 `/tmp/gw.log` 中 `dify.*api.*key` / `sk-[a-zA-Z]`：**无匹配**
- **结论：当前日志中未发现 API key 泄漏 ✅**

---

## 7. 前端就绪

### 7.1 学生端 H5 (student-app)
- `apps/student-app/` **不存在 `dist/` 或 `build/` 目录**
- 源码中 `API_BASE = ''`，依赖 vite dev proxy (`/api` → `192.168.100.165:8100`)
- **结论：学生端 H5 从未在服务器上构建，当前无可用生产包 🔴🔴**

### 7.2 教师端 H5 (teacher-app)
- `apps/teacher-app/dist/build/h5/` 存在
- 最后构建时间：**Apr 14 01:30**
- 包含 `index.html` + `assets/`
- **结论：教师端构建包存在，但已 14 天未更新 ⚠️**

### 7.3 入口 URL
- 开发环境：`http://192.168.100.165:8100`（vite proxy 指向）
- WebSocket 回退：`192.168.100.165:8100`
- **生产环境入口 URL 未配置**，无 nginx 反向代理或静态文件服务指向两个前端

---

## 8. 内测前必修清单（按风险排序）

| 风险等级 | 项目 | 修复建议 | 工作量 |
|---|---|---|---|
| 🔴 **阻塞** | **学生端 H5 无构建产物** | 在服务器执行 `npm run build:h5`，确认 `dist/build/h5/` 生成，并配置 nginx 静态服务 | 0.5 h |
| 🔴 **阻塞** | **内测账号缺口：仅 3 名学生** | 批量导入目标班级（30~50 人）+ 辅导员，导入后重置密码或强制首次登录修改 | 2~4 h |
| 🔴 **阻塞** | **无数据库自动备份** | 编写 `pg_dump` 脚本 + crontab 每日凌晨备份，保留 7 天滚动 | 1 h |
| 🔴 **阻塞** | **Gateway 无自动重启** | 编写 systemd service unit（`Restart=on-failure`），替换 nohup 启动 | 1 h |
| 🟡 **强烈建议** | **无 HTTPS / SSL** | nginx 配置反向代理 + Let's Encrypt / 自签名证书，或至少在内网使用 HTTPS | 2~4 h |
| 🟡 **强烈建议** | **防火墙关闭 (ufw inactive)** | 启用 ufw，仅开放 80/443/22（如有需要），关闭 5432/6379/8100 公网暴露 | 0.5 h |
| 🟡 **强烈建议** | **登录无 rate limit** | 在 `/api/auth/login` 增加 IP 级限流（如 5 次/分钟错误密码后 429） | 1~2 h |
| 🟡 **强烈建议** | **默认密码风险 2/3** | 批量导入时生成随机初始密码，或强制首次登录修改密码 | 1 h |
| 🟡 **强烈建议** | **JWT TTL 72 小时过长** | 缩短 `ACCESS_TOKEN_EXPIRE_MINUTES` 至 8~24 小时 | 0.2 h |
| 🟡 **强烈建议** | **config.py 存在硬编码密钥回退** | 删除 `jwt_secret` 默认值，启动时若环境变量缺失直接抛异常 | 0.2 h |
| 🟡 **强烈建议** | **日志无持久化与切割** | 将日志从 `/tmp` 移至 `/var/log/`，配置 logrotate | 0.5 h |
| 🟢 **可选** | **CORS 未配置** | 若 H5 部署在与 API 不同域名，需配置 `CORSMiddleware` + `allow_origins` | 0.5 h |
| 🟢 **可选** | **教师端构建已 14 天未更新** | 重新构建 teacher-app 并验证 | 0.5 h |

---

## 9. 总体评估

### 是否可以内测？
> **No — 当前存在多项阻塞项，不能直接启动内测。**

### 关键阻塞项
1. **学生端前端未构建** — 用户无入口可用。
2. **测试数据仅有 3 名学生** — 无法满足 30~50 人班级规模的内测。
3. **无自动备份 + 无进程守护** — 一旦 crash 或数据丢失，内测直接中断。

### 建议行动顺序
1. **立即（今天）**：构建 student-app → `dist/build/h5/`，nginx 加静态 location。
2. **立即（今天）**：批量导入目标班级学生账号 + 辅导员；重置默认密码。
3. **今天**：编写 systemd unit 替换 nohup；配置 `Restart=on-failure`。
4. **今天**：配置 `pg_dump` + crontab 每日备份。
5. **本周内**：启用 ufw / iptables，关闭 5432/6379/8100 对外；nginx 反向代理 + HTTPS。
6. **本周内**：登录接口加 rate limit；缩短 JWT TTL；删除硬编码密钥回退。

> **预计修阻塞项工作量：约 1 天（2 人日）。完成后可进入封闭内测。**
