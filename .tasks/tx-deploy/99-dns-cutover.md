# 阶段 99 · DNS 切换 + HTTPS(域名迁移完成后做)

## 前置条件

- 阶段 A-H 已完成,`http://82.156.129.75/` 和 `:81/` 可访问,`08-verify.sh` 全绿
- 域名的 DNS 管理面板可操作(xiaoguan.site / 130814.xyz)
- 腾讯云安全组已开 443

## 1. 降 TTL 提前一天

在 DNS 面板把 A 记录 TTL 从默认 600s 降到 60s,等 ~24 h 让缓存退役。

## 2. 切 A 记录

所有指向 64.90.13.65(HK)或 192.168.100.165 的域名,改为 `82.156.129.75`:

| 域名 | 用途 |
|---|---|
| `yxg.xiaoguan.site` | 学生端 |
| `teacher.xiaoguan.site` | 教师端 |
| `dify.xiaoguan.site` | Dify console + API |
| (可选)`yxg.130814.xyz` | 如果以前有,确认是否仍需要 |

**观察**:`nslookup yxg.xiaoguan.site 8.8.8.8` 过 1 min 后应看到新 IP。

## 3. 改 nginx server_name

ssh tx-new → `sudo vim /etc/nginx/sites-available/yixiaoguan`:

```nginx
# 学生端 :80(临时保留,签完证书后改为 301 redirect to 443)
server {
    listen 80;
    server_name yxg.xiaoguan.site;
    ...
}

# 教师端 从 :81 迁到独立域名
server {
    listen 80;
    server_name teacher.xiaoguan.site;
    root /var/www/yixiaoguan/teacher;
    ...
}

# Dify 新增一个 server
server {
    listen 80;
    server_name dify.xiaoguan.site;
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    # Dify API 直接走 :5001,还是通过 3000 的 nginx 容器,参考 ub 配置
    location /console/api/ {
        proxy_pass http://127.0.0.1:3000;
        ...
    }
}
```

然后:

```bash
sudo nginx -t && sudo systemctl reload nginx
curl -I http://yxg.xiaoguan.site/       # 应 200 (DNS 指向新机了)
```

## 4. certbot 签三张证书

```bash
sudo certbot --nginx \
    -d yxg.xiaoguan.site \
    -d teacher.xiaoguan.site \
    -d dify.xiaoguan.site \
    --agree-tos --no-eff-email -m your@email.com

# certbot 会自动改 nginx 配置,加 80 → 443 redirect,加 443 server block + ssl cert
```

验证:

```bash
curl -I https://yxg.xiaoguan.site/
certbot certificates | grep Expiry    # 应 90 天后到期
```

## 5. centrifugo allowed_origins 加 https

编辑 `/home/easten/dev/yixiaoguan-v2/deploy/centrifugo-config.json`,
`client.allowed_origins` 数组里加:

```json
"https://yxg.xiaoguan.site",
"https://teacher.xiaoguan.site"
```

然后:

```bash
cd /home/easten/dev/yixiaoguan-v2/deploy
docker compose -f docker-compose.centrifugo.yml restart
```

## 6. 验证 HTTPS 全路径

```bash
curl -I https://yxg.xiaoguan.site/                    # 200
curl -I https://yxg.xiaoguan.site/api/colleges        # 200
curl -I https://teacher.xiaoguan.site/                # 200

# Websocket
curl -sI https://yxg.xiaoguan.site/centrifugo/connection/websocket -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test=="
# 应 101 Switching Protocols 或 400
```

浏览器打开学生端,F12 看 WebSocket 到 `wss://yxg.xiaoguan.site/centrifugo/connection/websocket` 是否连通。

## 7. 旧机下线

稳定观察 1-2 天后:

```bash
# 165(内网,可保留作开发测试)
# HK 64.90.13.65:如果不再用,云厂商控制台销毁
```

## 8. 证书自动续期

certbot 装好会自动加 systemd timer:

```bash
systemctl list-timers | grep certbot
sudo certbot renew --dry-run   # 测试续期逻辑
```
