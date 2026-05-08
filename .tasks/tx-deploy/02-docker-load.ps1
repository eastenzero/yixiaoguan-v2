# RUN ON: local PowerShell
# 阶段 B · scp docker-images.tar.zst -> tx-new -> docker load
#
# 依赖:
#   - scp/ssh 在 PATH(OpenSSH for Windows)
#   - ssh config 里 tx-new 已配好(无需密码)
#   - 阶段 A 已完成(tx-new 上 easten 用户已加入 docker 组)
#
# 时长:scp 约 3-5 min(上行 10MB/s),load 约 5-10 min

$ErrorActionPreference = 'Stop'
$BACKUP = "G:\hk-et-backup-20260507\raw\blocks\docker-images.tar.zst"
$TX = "tx-new"
$REMOTE_PATH = "/home/easten/docker-images.tar.zst"

function Log($msg) { Write-Host "[B] $msg" -ForegroundColor Cyan }
function Ok($msg)  { Write-Host "[OK] $msg" -ForegroundColor Green }
function Warn($m)  { Write-Host "[WARN] $m" -ForegroundColor Yellow }

Log "== 1. 验证本地备份文件 =="
if (-not (Test-Path $BACKUP)) {
    throw "未找到 $BACKUP"
}
$size = (Get-Item $BACKUP).Length / 1GB
Ok ("local tarball: {0:F2} GB" -f $size)

Log "== 2. 验证 tx-new 可达 + docker 可用 =="
$probe = ssh $TX "docker version --format '{{.Server.Version}}' && df -h /home 2>&1 | head -2" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "tx-new 不可达或 docker 未起,先跑阶段 A"
}
Write-Host $probe

Log "== 3. scp 上传(as easten) =="
# 优先用 easten 账号,节省后续 chown
Log "正在上传 docker-images.tar.zst → $TX : $REMOTE_PATH (约 3-5 min)"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
scp $BACKUP "easten@${TX}:$REMOTE_PATH"
if ($LASTEXITCODE -ne 0) { throw "scp 失败" }
$sw.Stop()
Ok ("scp 完成,耗时 {0:F1} min" -f ($sw.Elapsed.TotalMinutes))

Log "== 4. 远端 sha256 校验 =="
$expectedSha = (Get-FileHash -Algorithm SHA256 $BACKUP).Hash.ToLower()
$remoteSha = (ssh $TX "sha256sum $REMOTE_PATH | cut -d' ' -f1" 2>&1).Trim()
if ($remoteSha -ne $expectedSha) {
    throw "sha256 不一致! local=$expectedSha remote=$remoteSha"
}
Ok "sha256 一致: $expectedSha"

Log "== 5. 远端 docker load =="
Log "正在解压 + load 镜像(约 5-10 min,2GB 压缩)"
$sw2 = [System.Diagnostics.Stopwatch]::StartNew()
ssh $TX "zstd -dc $REMOTE_PATH | docker load 2>&1 | tail -20"
if ($LASTEXITCODE -ne 0) { throw "docker load 失败" }
$sw2.Stop()
Ok ("docker load 完成,耗时 {0:F1} min" -f ($sw2.Elapsed.TotalMinutes))

Log "== 6. 补齐业务库需要的 pg16 + redis7(备份里是 pg15/redis6) =="
ssh $TX "docker pull postgres:16-alpine && docker pull redis:7-alpine" 2>&1 | Select-Object -Last 5
if ($LASTEXITCODE -ne 0) {
    Warn "docker pull 失败(可能网络慢);可后续单独重试"
}

Log "== 7. 最终镜像清单 =="
ssh $TX "docker images --format '{{.Repository}}:{{.Tag}}  {{.Size}}' | sort"

Log "== 8. 清理上传的 tarball(可选,释放 2GB) =="
$answer = Read-Host "删除 $TX 上的 $REMOTE_PATH 吗? [y/N]"
if ($answer -eq 'y' -or $answer -eq 'Y') {
    ssh $TX "rm -f $REMOTE_PATH"
    Ok "已清理"
} else {
    Warn "保留;释放空间时手动 ssh tx-new 'rm $REMOTE_PATH'"
}

Ok "阶段 B 完成"
Write-Host ""
Write-Host "下一步: ssh tx-new -l easten,跑 03-pg-start.sh"
