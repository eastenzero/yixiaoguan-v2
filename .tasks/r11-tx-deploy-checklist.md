# R11 内测访客模式部署清单

适用 commit 范围：`94a3c29..HEAD`（R11 G1 → 全部）

## 1. 后端 .env 新增变量

在 165 服务器（gateway .env，路径示例 `/home/easten/.../services/gateway/.env`）追加：

```dotenv
# Pilot 内测匿名模式开关（不开则 /api/auth/pilot-anonymous 返回 403）
PILOT_MODE_ENABLED=true

# Centrifugo subscribe proxy 共享密钥（与 centrifugo-config.json 同步）
CENTRIFUGO_PROXY_SECRET=<生成32位随机串，例 openssl rand -hex 16>
```

如果 settings 字段读环境变量名不一致（例如 pydantic v2 自动 upper），实际看 `app/config.py` 里的字段名，按它的 alias 决定 env 名。

## 2. Centrifugo 配置改动

修改 `deploy/centrifugo-config.json`：
- 文件已被 G4 / Review-Fix commit 修改，TX 拉取后该文件自动是新版
- secret 现在通过 `proxy_static_http_headers.X-Auth` 传递，**不在 URL query 里**（避免日志泄露）
- 把 `CHANGE_ME_SYNC_WITH_CENTRIFUGO_PROXY_SECRET` 占位替换成与 gateway `.env` 中 `CENTRIFUGO_PROXY_SECRET` 同样的随机串
- **更安全的做法**：直接通过环境变量注入（不修改 git 里的 config.json）：
  ```bash
  export CENTRIFUGO_PROXY_STATIC_HTTP_HEADERS='{"X-Auth": "<actual_random_secret>"}'
  ```
  并把 docker-compose.yml 里 centrifugo 服务的 environment 加这一项。这种情况下 config.json 里的 X-Auth 值可以保持占位。
- 拉取后 restart centrifugo 即可

## 3. 数据库 migration

在 gateway 目录下：
```bash
ssh ub
cd ~/yixiaoguan-v2/services/gateway
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

## 5. 重启服务（顺序很重要）

```bash
# Step 1: 先重启 gateway（让新 endpoint + 新 model 生效）
sudo systemctl restart yixiaoguan-gateway

# 健康检查
curl http://localhost:8100/health

# Step 2: 再重启 centrifugo（让 proxy 配置生效）
docker compose -f deploy/docker-compose.yml restart centrifugo

# 看 centrifugo 日志确认有 "subscribe proxy" 字样
docker logs --tail 30 deploy_centrifugo_1 2>&1 | grep -i proxy
```

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
4. centrifugo 配置恢复：`git checkout 8a4cebe -- deploy/centrifugo-config.json`，如果你用了 `CENTRIFUGO_PROXY_STATIC_HTTP_HEADERS` 环境变量注入，也要同步移除/恢复该环境变量；然后再 `docker compose restart centrifugo`

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
