# TX-NEW 公网部署(医小管 V2 · R11 内测版)

> 目标机:`tx-new` = `82.156.129.75` (Ubuntu 24.04.4 LTS / x86_64 / 4C 7.4G / 108G free)
> 源机:`ub` = `192.168.100.165` (内网 R11 已验证)
> 策略:**纯 IP 先上线**,域名/HTTPS 延迟做(等 DNS 切换)
> 备份:`G:\hk-et-backup-20260507\` 只取 `docker-images.tar.zst` 加速 Dify 镜像加载

## 在哪里执行

每个脚本开头都标了 `# RUN ON: <host>`。大致:

| 脚本 | 执行位置 |
|---|---|
| `01-base-install.sh` | **tx-new**(root) |
| `02-docker-load.ps1` | **本地 PowerShell**(scp + 触发远程 docker load) |
| `03-pg-start.sh` | **tx-new**(easten)|
| `03b-pg-migrate.ps1` | **本地 PowerShell**(ub dump → scp → tx restore) |
| `04-dify-migrate.ps1` | **本地 PowerShell**(rsync + dump 中转) |
| `05-gateway.sh` | **tx-new**(easten) |
| `06-centrifugo.sh` | **tx-new**(easten) |
| `07-nginx-ip.sh` | **tx-new**(root + easten) |
| `08-verify.sh` | **tx-new**(easten) |
| `99-dns-cutover.md` | 等域名切换时再做 |

## 执行顺序(逐阶段暂停确认)

```
[阶段 0 · 手工] 腾讯云控制台 → 安全组 → 入站放行 TCP 80 (22 已开)
[阶段 A] 01-base-install.sh          # apt install + 建 easten 用户 + docker group
[阶段 B] 02-docker-load.ps1          # scp 2GB docker-images.tar.zst → load
[阶段 C] 03-pg-start.sh              # 起 yx_postgres + yx_redis
         03b-pg-migrate.ps1          # 从 ub 迁移 yixiaoguan_v2 数据
[阶段 D] 04-dify-migrate.ps1         # rsync dify-deploy + pg_dumpall dify+dify_plugin
[阶段 E] 05-gateway.sh               # git clone + venv + alembic + systemd
[阶段 F] 06-centrifugo.sh            # deploy/.env + docker compose
[阶段 G] 07-nginx-ip.sh              # nginx IP 模式(学生 80 / 教师 81)
[阶段 H] 08-verify.sh                # 9 项端到端验证
───────── 此时 http://82.156.129.75/ 可访问 ─────────
[延迟]   99-dns-cutover.md           # DNS 切 + certbot HTTPS + 改 server_name
```

## 关键约定

- **运行用户**:`easten` (gateway、Dify、Centrifugo 都以它的身份运行)
- **仓库目录**:`/home/easten/dev/yixiaoguan-v2`
- **Dify 目录**:`/home/easten/dev/dify-deploy/docker`
- **静态站点**:`/var/www/yixiaoguan/{student,teacher}`(由 root 写,www-data 读)
- **端口**:nginx 80(学生)+ 81(教师) → gateway 127.0.0.1:8100 + centrifugo 127.0.0.1:8000
- **数据层**:yx_postgres 127.0.0.1:5432 + yx_redis 127.0.0.1:6379(docker,仅本地)
- **秘钥**:严禁写到 git。`services/gateway/.env` 和 `deploy/.env` 都是 gitignored

## 回滚

各阶段都是独立可重入的,失败后:
- 阶段 A/B:TX-NEW 清机(删 /home/easten + apt remove)
- 阶段 C:`docker compose -f deploy/docker-compose.yxdata.yml down -v`(⚠️ -v 删数据卷)
- 阶段 D:`cd ~/dev/dify-deploy/docker && docker compose down -v`
- 阶段 E/F:`systemctl stop yixiaoguan-gateway` + `docker compose down`
- 阶段 G:`sudo rm /etc/nginx/sites-enabled/yixiaoguan && sudo systemctl reload nginx`

## 不在本套脚本范围

- EasyTier mesh / coturn / mtg / mihomo / lifeos / webrtc-relay(TX-NEW 不部署)
- G 盘 V1 业务库 yxg_v2 的恢复(schema 不兼容,**不要** restore)
- 证书 / DNS 切换(见 `99-dns-cutover.md`)
