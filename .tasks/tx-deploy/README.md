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

---

## 执行经验回顾(2026-05-09 实际部署)

第一次完整跑下来,踩过的坑和真实修法:

### 1. apt 包名 (Ubuntu 24.04)

`docker-compose-plugin` 是 Docker 官方 apt 源里的名字,腾讯云 Ubuntu 镜像没有。
正确包名:`docker-compose-v2 docker-buildx`(见 `01-base-install.sh`)。

### 2. github 国内 TLS 不通

`git clone https://github.com/...` 在 tx-new 上会 `GnuTLS recv error (-110)`。
绕开:用 `git bundle` 中转。

```powershell
# 本地 PowerShell
git bundle create $env:TEMP\repo.bundle --all
scp $env:TEMP\repo.bundle easten@tx-new:/home/easten/repo.bundle
ssh tx-new "cd /home/easten/dev && git clone /home/easten/repo.bundle yixiaoguan-v2"
```

`03-pg-start.sh` 已删除自动 git clone 步骤,改为前置假设。

### 3. docker hub 国内不通 + docker 29 daemon.json bug

`docker pull postgres:16-alpine` 会 timeout(连 docker hub `registry-1.docker.io` 失败)。
`/etc/docker/daemon.json` 配 registry-mirrors 在 **docker.io 29.x** 上会触发解析 bug
(`invalid character ':' in string escape code`),导致 docker daemon 起不来。

**实际修法**:从 ub `docker save postgres:16-alpine redis:7-alpine | zstd > /tmp/pg16-redis7.tar.zst`,
scp 中转到 tx-new `docker load`(见阶段 B)。

### 4. pip install 慢

默认走 pypi.org 国内极慢。配腾讯云内部 mirror(同机房,免外网流量):

```bash
mkdir -p ~/.pip && cat > ~/.pip/pip.conf <<'EOF'
[global]
index-url = https://mirrors.cloud.tencent.com/pypi/simple
trusted-host = mirrors.cloud.tencent.com
timeout = 60
EOF
```

整个 gateway requirements 从 5+ min 降到 31s。

### 5. Dify api worker 第一次启动 hang

ub 备份恢复后第一次起 `docker-api-1`,gunicorn master 起来 listen :5001,
但 `Booting worker` 日志没出现,worker 卡在初始化(可能在等 plugin_daemon ready)。
`/v1/parameters` 5 秒超时,gateway `/health` 因此 5 秒后才返(dify=error)。

**修法**:`docker restart docker-api-1` 一次,worker 正常 boot,API 立即恢复。

### 6. 实际跑通的脚本(主流程)

> 部分原 `.ps1` 脚本(`03b-pg-migrate.ps1`、`04-dify-migrate.ps1`、`05-gateway.sh` 含交互 `read`)
> 在实际部署中没有直接跑 — 流程被拆成更小的 ssh 链命令。
> 它们保留作为完整流程参考;**实际可复用脚本**:

| 脚本 | 用途 |
|---|---|
| `01-base-install.sh` | 阶段 A,直接跑 |
| `03-pg-start.sh` | 阶段 C1,直接跑(前提:repo 已通过 bundle 中转) |
| `03c-pg-restore.sh` | 阶段 C2,前提 dump 已 scp 到 `/tmp/yxg_v2.dump` |
| `04b-dify-restore.sh` | 阶段 D2,前提 dump 已 scp 到 `/tmp/dify-all.sql.zst` 且 docker compose up 完成 |
| `05-gateway-bringup.sh` | 阶段 E,前提 `services/gateway/.env` 已就位、venv 装完 |
| `06-centrifugo.sh` | 阶段 F,直接跑 |
| `06b-centrifugo-verify.sh` | 阶段 F 后的联通性验证 |
| `07-nginx-ip.sh` | 阶段 G,前提 `/tmp/student/`、`/tmp/teacher/` dist 已上传 |
| `08-verify.sh` | 阶段 H,12 项端到端验证 |

### 7. ub gateway `.env` 关键字段(必须从 ub 拷贝)

下列字段在 `services/gateway/.env` 必须保留 ub 上的真实值(否则 Dify chatflow 调用失败):

- `dify_api_key`(医小管-主对话流的 app api key)
- `dify_global_dataset_id`(global-kb-v2 dataset id,UUID)
- `dify_dataset_api_key`(dataset 检索/上传 api key)
- `jwt_secret`(保留 ub 值可让旧 token 仍有效;换值则所有用户重登)

获取方式:`scp ub:/home/easten/dev/yixiaoguan-v2/services/gateway/.env $env:TEMP\ub-gw.env`,
然后从中读取(读完务必删本地副本)。

业务 DB 用户(`yxg`)密码通过整库 dump-restore 自动保持一致(password 存在 pg_authid 表),
所以 tx-new 的 gateway `.env` 里 `database_url` 写的密码 = ub 上的同名密码。

### 8. 数据规模实测(参考)

- yixiaoguan_v2 dump:132 KB,restore < 1 s
- Dify pg_dumpall (zstd):34 MB,restore 9 s
- dify-deploy/ tar(含 weaviate):182 MB
- docker images bundle(zst):2.0 GB,docker load 48 s

