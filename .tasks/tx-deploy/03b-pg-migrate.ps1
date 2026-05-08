# RUN ON: local PowerShell
# 阶段 C2 · 从 ub (165) dump yixiaoguan_v2 → scp 中转 → tx-new restore
#
# 依赖:
#   - ub 上 yx_postgres 容器在跑,yxg 用户 + yixiaoguan_v2 数据库存在
#   - tx-new 上 03-pg-start.sh 已完成(新 yx_postgres 起来但业务库空)
#   - ssh config 里 ub 和 tx-new 都配好
#
# 迁移内容:
#   - yixiaoguan_v2 库 (schema + data, pg_dump -Fc)
#   - yxg user(从 ub dump globals 拿到 password hash)

$ErrorActionPreference = 'Stop'

function Log($m) { Write-Host "[C2] $m" -ForegroundColor Cyan }
function Ok($m)  { Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }

# ===== 临时中转目录 =====
$TMP = "$env:TEMP\tx-pg-migrate"
New-Item -ItemType Directory -Path $TMP -Force | Out-Null

# ===== 1. 在 ub dump =====
Log "== 1. ub (165) dump yixiaoguan_v2 + yxg role =="
# dump globals 获取 yxg role(含密码 hash) — 用 yx_admin(superuser)
ssh ub @"
set -e
docker exec yx_postgres pg_dumpall -U yx_admin --roles-only > /tmp/yxg-roles.sql
docker exec yx_postgres pg_dump -U yx_admin -Fc --no-owner --no-acl -d yixiaoguan_v2 -f /tmp/yixiaoguan_v2.dump
ls -lh /tmp/yxg-roles.sql /tmp/yixiaoguan_v2.dump
docker cp yx_postgres:/tmp/yxg-roles.sql /tmp/yxg-roles.sql
docker cp yx_postgres:/tmp/yixiaoguan_v2.dump /tmp/yixiaoguan_v2.dump
"@
if ($LASTEXITCODE -ne 0) { throw "ub dump 失败" }
Ok "ub dump 完成"

# ===== 2. scp 到本地中转 =====
Log "== 2. scp ub:/tmp/*.{sql,dump} → local =="
scp "ub:/tmp/yxg-roles.sql" "$TMP/"
scp "ub:/tmp/yixiaoguan_v2.dump" "$TMP/"
$dumpSize = (Get-Item "$TMP/yixiaoguan_v2.dump").Length / 1MB
Ok ("dump 文件大小: {0:F2} MB" -f $dumpSize)

# ===== 3. scp 到 tx-new =====
Log "== 3. scp local → tx-new:/tmp =="
scp "$TMP/yxg-roles.sql" "tx-new:/tmp/"
scp "$TMP/yixiaoguan_v2.dump" "tx-new:/tmp/"
Ok "已到 tx-new"

# ===== 4. 拿到 ub 上的 yxg 密码(gateway .env 里明文) =====
Log "== 4. 从 ub 读 gateway .env 的 DATABASE_URL =="
$ubEnv = ssh ub "grep '^database_url=' ~/dev/yixiaoguan-v2/services/gateway/.env 2>/dev/null"
if (-not $ubEnv) { throw "ub 上找不到 gateway .env 的 database_url" }
# 解析 postgresql+asyncpg://yxg:PASSWORD@host:port/db
if ($ubEnv -match ':\/\/([^:]+):([^@]+)@') {
    $yxgUser = $Matches[1]
    $yxgPass = $Matches[2]
    Ok "拿到 yxg 密码(长度 $($yxgPass.Length))"
} else {
    throw "无法解析 database_url: $ubEnv"
}

# 同时拿 redis 密码
$ubRedis = ssh ub "grep '^redis_url=' ~/dev/yixiaoguan-v2/services/gateway/.env 2>/dev/null"
$ubDify = ssh ub "grep -E '^dify_(api_url|api_key|global_dataset_id|dataset_api_key)=' ~/dev/yixiaoguan-v2/services/gateway/.env 2>/dev/null"

# ===== 5. 在 tx-new 上 restore =====
Log "== 5. tx-new restore: 建 yxg 用户 + yixiaoguan_v2 库 + pg_restore =="
ssh tx-new @"
set -e
# 把文件拷进容器(方便 psql/pg_restore 直接用)
docker cp /tmp/yxg-roles.sql yx_postgres:/tmp/yxg-roles.sql
docker cp /tmp/yixiaoguan_v2.dump yx_postgres:/tmp/yixiaoguan_v2.dump

# 5a. 建 yxg 用户(用 ub 同样的明文密码,保持 .env 可互换)
docker exec yx_postgres psql -U yx_admin -tc "SELECT 1 FROM pg_roles WHERE rolname='$yxgUser'" | grep -q 1 || \
  docker exec yx_postgres psql -U yx_admin -c "CREATE USER $yxgUser WITH PASSWORD '$yxgPass';"

# 5b. 建库(owner=yxg)
docker exec yx_postgres psql -U yx_admin -tc "SELECT 1 FROM pg_database WHERE datname='yixiaoguan_v2'" | grep -q 1 || \
  docker exec yx_postgres psql -U yx_admin -c "CREATE DATABASE yixiaoguan_v2 OWNER $yxgUser;"

# 5c. restore 数据
docker exec yx_postgres pg_restore -U yx_admin -d yixiaoguan_v2 --no-owner --role=$yxgUser /tmp/yixiaoguan_v2.dump 2>&1 | tail -15 || echo '[WARN] 部分错误可忽略(如果只是 grant 到不存在的 role)'

# 5d. 验证
echo '--- 表清单 ---'
docker exec yx_postgres psql -U $yxgUser -d yixiaoguan_v2 -c '\dt' | tail -20
echo '--- 数据量 ---'
docker exec yx_postgres psql -U $yxgUser -d yixiaoguan_v2 -tA -c "
SELECT 'users=' || COUNT(*) FROM users;
SELECT 'pilot_users=' || COUNT(*) FROM users WHERE staff_id LIKE 'pilot:%';
SELECT 'feedbacks=' || COUNT(*) FROM feedbacks;
SELECT 'events=' || COUNT(*) FROM events;
SELECT 'kb_entries=' || COUNT(*) FROM kb_entries;
SELECT 'colleges=' || COUNT(*) FROM colleges;
"

# 5e. 清 tmp
docker exec yx_postgres rm -f /tmp/yxg-roles.sql /tmp/yixiaoguan_v2.dump
rm -f /tmp/yxg-roles.sql /tmp/yixiaoguan_v2.dump
"@
if ($LASTEXITCODE -ne 0) { throw "tx-new restore 失败" }
Ok "tx-new restore 完成"

# ===== 6. 保存关键配置到本地 tmp,供阶段 E gateway .env 引用 =====
Log "== 6. 保存 ub 的 gateway .env 关键字段到本地 $TMP\gateway-env-from-ub.txt =="
@"
# 从 ub 复制,阶段 E 生成 tx-new 的 .env 时参考
$ubEnv
$ubRedis
$ubDify
"@ | Out-File -Encoding utf8 "$TMP\gateway-env-from-ub.txt"
Ok "已保存到 $TMP\gateway-env-from-ub.txt(敏感,别泄漏)"

# ===== 7. 清理 ub 侧 dump =====
Log "== 7. 清理 ub 侧 dump 文件 =="
ssh ub "rm -f /tmp/yxg-roles.sql /tmp/yixiaoguan_v2.dump"
Ok "ub 侧已清"

Ok "阶段 C2 完成"
Write-Host ""
Write-Host "下一步: 跑 04-dify-migrate.ps1 迁移 Dify"
