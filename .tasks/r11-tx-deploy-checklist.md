# R11 内测访客模式部署清单

适用 commit 范围：`94a3c29..HEAD`（R11 G1 → 全部，11 个 commit）

## 0. 165 上的实际路径（已实测）

- 仓库目录：`/home/easten/dev/yixiaoguan-v2`
- gateway systemd 服务：`yixiaoguan-gateway.service`（已运行）
- nginx 站点配置：`/etc/nginx/sites-enabled/yixiaoguan`
- **Centrifugo 当前未部署**（无容器、无 nginx location），本次部署需要**首次启动**

后续命令默认在仓库目录下执行：
```bash
ssh ub
cd ~/dev/yixiaoguan-v2
git pull
```

## 1. 后端 .env 新增变量

在 `services/gateway/.env` 追加：

```dotenv
# Pilot 内测匿名模式开关（不开则 /api/auth/pilot-anonymous 返回 403）
PILOT_MODE_ENABLED=true

# Centrifugo subscribe proxy 共享密钥（与 centrifugo-config.json 同步）
CENTRIFUGO_PROXY_SECRET=<生成32位随机串，例 openssl rand -hex 16>
```

如果 settings 字段读环境变量名不一致（例如 pydantic v2 自动 upper），实际看 `app/config.py` 里的字段名，按它的 alias 决定 env 名。

## 2. Centrifugo 首次启动

165 上 centrifugo 之前没部过，本次需要**首次启动**容器并把 nginx location 接入。

### 2.1 准备 deploy/.env（centrifugo compose 用）

`deploy/.env` 用于 docker-compose.centrifugo.yml 读取。如果文件不存在，按 `.env.example` 创建：
```bash
cd ~/dev/yixiaoguan-v2/deploy
cp .env.example .env  # 如已有则跳过
```

编辑 `deploy/.env`，至少包含：
```dotenv
CENTRIFUGO_SECRET=<生成32位随机串，用于 client JWT HMAC>
CENTRIFUGO_API_KEY=<生成32位随机串，用于 server API>
# proxy 静态 header 注入（强烈推荐，避免改 git 里的 config.json）
CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS={"X-Auth": "<同 gateway .env 的 CENTRIFUGO_PROXY_SECRET>"}
```

注意 `CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS` 是 JSON 字符串，等号后面**不要加引号**。

### 2.2 让 docker-compose.centrifugo.yml 透传 PROXY HEADERS env

检查 `deploy/docker-compose.centrifugo.yml`，确认 `environment` 块包含 `CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS=${CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS}`。如果当前还没有该行，需要追加：
```yaml
    environment:
      - CENTRIFUGO_CLIENT_TOKEN_HMAC_SECRET_KEY=${CENTRIFUGO_SECRET}
      - CENTRIFUGO_HTTP_API_KEY=${CENTRIFUGO_API_KEY}
      - CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS=${CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS}
```
（如果 R11 review-fix commit 已加，则跳过；TX 拉取后自查一下。）

### 2.3 启动容器

```bash
cd ~/dev/yixiaoguan-v2/deploy
docker compose -f docker-compose.centrifugo.yml up -d

# 看启动日志
docker logs --tail 50 yxg-centrifugo
# 确认无 panic / config error；预期看到 listening on :8000 + subscribe_proxy enabled
```

### 2.4 接入 nginx

把 `deploy/nginx-centrifugo.conf` 的 location 块加到 `/etc/nginx/sites-enabled/yixiaoguan` 中**所有 server block**（学生端 `yxg.xiaoguan.site` + 教师端 `teacher.xiaoguan.site`）：
```bash
# 编辑
sudo vim /etc/nginx/sites-enabled/yixiaoguan
# 在每个 server { ... } 中追加 deploy/nginx-centrifugo.conf 的 location /centrifugo/ 块

# 测试 + reload
sudo nginx -t && sudo systemctl reload nginx
```

### 2.5 备选方案：把 secret 写到 config.json（不推荐）

如果不想用 env 注入，也可以直接编辑 `deploy/centrifugo-config.json`：把 `proxy_static_http_headers.X-Auth` 的占位替换成与 gateway `.env` 中 `CENTRIFUGO_PROXY_SECRET` 同样的随机串。但配置写到 git 跟踪的文件里有泄露风险，**优先选 §2.1 的 env 注入**。

## 3. 数据库 migration

```bash
cd ~/dev/yixiaoguan-v2/services/gateway
source venv/bin/activate
alembic upgrade head
```

预期会执行两个新 migration：
- `3fd32d018c9c_add_r11_pilot_tables.py`（创建 feedbacks / unanswered_user_feedback / events 三张表）
- `11f120f3ef96_add_chat_analytics_cost_columns.py`（chat_analytics 加 8 列）

跑完后用 `alembic current` 确认 head 是 `11f120f3ef96`。

## 4. Python 依赖

requirements.txt 加了 `slowapi>=0.1.9`，TX 拉取后：
```bash
pip install -r requirements.txt
```

## 5. 重启 gateway

```bash
sudo systemctl restart yixiaoguan-gateway

# 健康检查
curl http://localhost:8100/health

# 看启动日志确认无 ImportError / 配置错误
sudo journalctl -u yixiaoguan-gateway -n 50 --no-pager
```

注意 centrifugo 在 §2 已启动；如果改了 deploy/.env 里的 secret，需要 `docker compose -f deploy/docker-compose.centrifugo.yml restart` 让新 env 生效。

## 6. 烟囱测试（pilot 流程端到端）

### 6.1 后端单点测试

```bash
# 拿一个 device_id 试 pilot 登录
curl -X POST http://localhost:8100/api/auth/pilot-anonymous \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-device-12345678"}'
# 期望：200 + access_token

# 用 token 拉学院列表（免登录但带 token 也行）
curl http://localhost:8100/api/colleges
# 期望：200 + 21 条 colleges

# 用 token 试 chat（注意会消耗 Dify 额度）
TOKEN=<上面拿到的 access_token>
curl -X POST http://localhost:8100/api/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"医务室在哪","conv_id":null}'
# 期望：SSE 流式返回；可能有 unanswered_invite 事件
```

### 6.2 限流测试

连续快速调 11 次 /api/chat/send（同一 token），第 11 次应该返回 **429 + Retry-After**。

### 6.3 admin 防御测试

教师 token 调 /api/admin/users/import，body 包含 `staff_id: "pilot:abc"`，期望 **400 + "staff_id 不能以 'pilot:' 开头"**。

### 6.4 Centrifugo proxy 测试

用 conv_id=999999（不存在）订阅 `conv:999999` 频道，期望 centrifugo 返回订阅失败（403/forbidden）。
看 gateway 日志应有 `centrifugo subscribe check failed` 或 deny 记录。

### 6.5 数据看板成本卡片

教师端打开 /pages/analytics/index 页，应能看到"AI 成本"卡片：
- 总 tokens
- 总价格
- 平均 latency
- 按日条形图

如果是空数据（chat_analytics 没新数据），卡片显示 0 但不报错。

## 7. 前端构建

学生端：
```bash
cd apps/student-app
pnpm install  # 如果有新依赖
pnpm build:h5  # 或对应命令
```

教师端：
```bash
cd apps/teacher-app
pnpm install
pnpm build:h5
```

部署 dist 到 nginx。

## 8. 回滚方案

如果发现严重问题，按相反顺序回滚：

1. 关 pilot 模式：`PILOT_MODE_ENABLED=false` 后重启 gateway —— 阻止新 pilot 用户进入
2. 拉 commit `8a4cebe` checkout：`git checkout 8a4cebe -- services/gateway` —— 回滚后端代码
3. alembic downgrade：`alembic downgrade b2e7a91c4d80` —— 回滚两个 R11 migration
4. centrifugo 配置恢复：`git checkout 8a4cebe -- deploy/centrifugo-config.json`；如果用了 `CENTRIFUGO_CHANNEL_PROXY_SUBSCRIBE_HTTP_STATIC_HEADERS` 环境变量注入，也要同步移除该 env；然后 `docker compose -f deploy/docker-compose.centrifugo.yml down`（彻底关掉这个容器，因为 8a4cebe 之前没部署过）

注意：alembic downgrade 会 drop 表，**会丢失 R11 期间收集的反馈数据**。如果想保留：
- 先 SQL 备份：`pg_dump -t feedbacks -t unanswered_user_feedback -t events ... > r11-data.sql`
- 再 downgrade

## 9. 监控建议（pilot 期间）

每天看一次：
```sql
-- 反馈数量
SELECT COUNT(*) FROM feedbacks WHERE created_at >= now() - interval '1 day';
SELECT COUNT(*) FROM unanswered_user_feedback WHERE created_at >= now() - interval '1 day';

-- pilot 用户数
SELECT COUNT(*) FROM users WHERE staff_id LIKE 'pilot:%';

-- AI 成本（昨日）
SELECT SUM(total_price) AS price, SUM(total_tokens) AS tokens, COUNT(*) AS msgs
FROM chat_analytics
WHERE created_at >= current_date - interval '1 day' AND created_at < current_date;

-- 限流命中（看 gateway 日志）
grep "Rate limit exceeded" /var/log/yixiaoguan-gateway.log | wc -l
```
