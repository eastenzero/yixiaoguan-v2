# RUN ON: local PowerShell
# 阶段 D · 从 ub 迁移 Dify(rsync compose + volumes,pg_dumpall 数据)
#
# 依赖:
#   - 阶段 B 完成(tx-new 上已 docker load 得到 langgenius/dify-*:1.13.3 + pg15 + redis6 + nginx + weaviate + sandbox + ssrf_proxy)
#   - ub 上 Dify 全家桶在跑
#
# 注意:
#   - rsync volumes 时会包含 weaviate 向量索引(~50 MB)和 plugin_daemon 数据(~340 MB)
#   - db/data 里的 pgdata 不直接 rsync(跨容器路径可能有问题),
#     改用 pg_dumpall 更安全
#   - 本阶段约 10-15 min(rsync + pg dump/restore)

$ErrorActionPreference = 'Stop'
function Log($m) { Write-Host "[D] $m" -ForegroundColor Cyan }
function Ok($m)  { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }

$TMP = "$env:TEMP\tx-dify-migrate"
New-Item -ItemType Directory -Path $TMP -Force | Out-Null

# ===== 1. 探查 ub 上的 Dify 布局 =====
Log "== 1. 探查 ub Dify =="
$ubDifyDir = (ssh ub "docker inspect docker-api-1 --format '{{ index .Config.Labels \`"com.docker.compose.project.working_dir\`" }}'" 2>&1).Trim()
Log "ub Dify dir: $ubDifyDir"
if (-not $ubDifyDir -or $ubDifyDir -eq '<no value>') { throw "无法定位 ub Dify dir" }

# ===== 2. 停 ub Dify(保证数据一致) =====
Log "== 2. 停 ub Dify(拿一致快照) =="
Warn "ub 上 Dify 将停机 ~2 min(dump 期间)"
$confirm = Read-Host "确认停 ub Dify 吗? [y/N]"
if ($confirm -ne 'y' -and $confirm -ne 'Y') { throw "用户取消" }
ssh ub "cd $ubDifyDir && docker compose stop api worker worker_beat web plugin_daemon sandbox 2>&1 | tail -10"

# ===== 3. ub pg_dumpall(Dify 独立的 pg15) =====
Log "== 3. ub: pg_dumpall 从 docker-db_postgres-1 =="
ssh ub @"
set -e
docker exec docker-db_postgres-1 pg_dumpall -U postgres -c 2>/dev/null | zstd -T0 -3 > /tmp/dify-all.sql.zst
ls -lh /tmp/dify-all.sql.zst
"@
if ($LASTEXITCODE -ne 0) { throw "ub pg_dumpall 失败" }

# ===== 4. 重启 ub Dify(dump 完了) =====
Log "== 4. 重启 ub Dify =="
ssh ub "cd $ubDifyDir && docker compose start 2>&1 | tail -10"
Ok "ub Dify 已恢复"

# ===== 5. rsync ub:$ubDifyDir → local → tx-new =====
# 直接 ub → tx-new 需要 ub 有 tx-new 的 key,走中转更稳
Log "== 5. rsync ub compose 目录(不含 db 数据和 plugin_daemon 大 binary) =="
# Windows 下 rsync 不一定装;用 scp -rp 代替
$localDify = "$TMP\dify-deploy"
New-Item -ItemType Directory -Path $localDify -Force | Out-Null
ssh ub "cd $ubDifyDir/.. && tar --exclude='volumes/db/data/*' --exclude='volumes/app/storage/*' --exclude='volumes/redis/*' -cf - docker | zstd -T0 -3" | `
    zstd -d 2>$null > "$TMP\dify-deploy.tar"
if (-not (Test-Path "$TMP\dify-deploy.tar") -or (Get-Item "$TMP\dify-deploy.tar").Length -lt 1024) {
    # PS 的 | zstd -d 在 Windows 上可能不可用;fallback 直接 tar+scp
    Warn "PS 管道 zstd 不可用,fallback: 在 ub 打包 → scp"
    ssh ub "cd $ubDifyDir/.. && tar --exclude='volumes/db/data/*' --exclude='volumes/app/storage/*' --exclude='volumes/redis/*' -czf /tmp/dify-deploy.tar.gz docker"
    scp "ub:/tmp/dify-deploy.tar.gz" "$TMP\"
    ssh ub "rm -f /tmp/dify-deploy.tar.gz"
    Ok "下载完成 $TMP\dify-deploy.tar.gz"
    $localDifyTar = "$TMP\dify-deploy.tar.gz"
} else {
    Ok "下载完成 $TMP\dify-deploy.tar"
    $localDifyTar = "$TMP\dify-deploy.tar"
}

# 同时 scp dumpall
scp "ub:/tmp/dify-all.sql.zst" "$TMP\"
ssh ub "rm -f /tmp/dify-all.sql.zst"

# ===== 6. 上传到 tx-new =====
Log "== 6. 上传到 tx-new =="
$remoteDir = "/home/easten/dev"
ssh tx-new "mkdir -p $remoteDir"
scp $localDifyTar "tx-new:$remoteDir/dify-deploy.tar.gz"
scp "$TMP\dify-all.sql.zst" "tx-new:/tmp/"
Ok "已上传"

# ===== 7. tx-new 解包 + 起 Dify =====
Log "== 7. tx-new: 解包 Dify + compose up =="
ssh tx-new @"
set -e
cd /home/easten/dev
# 旧目录备份
[ -d dify-deploy ] && mv dify-deploy dify-deploy.bak.`$(date +%s)`
tar -xzf dify-deploy.tar.gz
rm -f dify-deploy.tar.gz
ls -la dify-deploy/docker | head -20

# 起
cd dify-deploy/docker
docker compose up -d
sleep 15
docker compose ps
"@
if ($LASTEXITCODE -ne 0) { throw "tx-new 起 Dify 失败" }
Ok "tx-new Dify 已起"

# ===== 8. 等 pg 容器 healthy,然后 restore =====
Log "== 8. 等 pg 容器 healthy 后 restore =="
ssh tx-new @"
set -e
# 等最多 60s
for i in {1..12}; do
  status=`$(docker inspect docker-db_postgres-1 --format '{{.State.Health.Status}}' 2>/dev/null || echo 'none')`
  echo "\[`$i`/12\] pg status: `$status`"
  [ "`$status`" = 'healthy' ] && break
  sleep 5
done

# restore(-c 会 drop existing,干净)
zstd -dc /tmp/dify-all.sql.zst | docker exec -i docker-db_postgres-1 psql -U postgres 2>&1 | tail -20
rm -f /tmp/dify-all.sql.zst

# 验证
docker exec docker-db_postgres-1 psql -U postgres -tA -c "SELECT datname FROM pg_database WHERE datistemplate=false;"
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT COUNT(*) FROM datasets;"
docker exec docker-db_postgres-1 psql -U postgres -d dify -tA -c "SELECT id, name FROM datasets;"

# 重启 api/worker 让 schema 生效
cd /home/easten/dev/dify-deploy/docker
docker compose restart api worker worker_beat
"@
if ($LASTEXITCODE -ne 0) { Warn "restore 中有错误,检查上面输出" }
Ok "阶段 D 完成"

Write-Host ""
Write-Host "下一步:"
Write-Host "  1. ssh tx-new 并跑 curl http://127.0.0.1/ -H 'Host: dify.xiaoguan.site' 看 Dify Web"
Write-Host "  2. 再跑 05-gateway.sh 部署 gateway"
