# dispatch-batch-3.ps1
# Launch 3 parallel Kimi jobs for R06 batch-3:
#   r06-4a (local Windows, Executor)
#   r06-2b (on 165 via SSH, Scout)
#   r06-5b (on 165 via SSH, Executor)
# Each job writes to a log file; PIDs saved to state JSON.
$ErrorActionPreference = "Stop"

$root    = "C:\Users\Administrator\Documents\code\yixiaoguan-v2"
$logDir  = Join-Path $root ".tasks\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$ts        = Get-Date -Format "yyyyMMdd-HHmmss"
$log4a     = Join-Path $logDir "r06-4a-$ts.log"
$log2b     = Join-Path $logDir "r06-2b-$ts.log"
$log5b     = Join-Path $logDir "r06-5b-$ts.log"
$statePath = Join-Path $logDir "batch-3-state.json"

# --- Job 1: r06-4a, local Kimi ---
$kimiExe = (Get-Command kimi -ErrorAction Stop).Source
$p4a = Start-Process -FilePath $kimiExe `
    -ArgumentList "--print", "-p", ".tasks\r06-4a-exec-gateway-inputs.md" `
    -WorkingDirectory $root `
    -RedirectStandardOutput $log4a `
    -RedirectStandardError "$log4a.err" `
    -PassThru -NoNewWindow

# --- Job 2: r06-2b, SSH to 165 ---
$cmd2b = "cd ~/dev/yixiaoguan-v2 && kimi --print -p .tasks/r06-2b-scout-dify-datasets.md < /dev/null"
$p2b = Start-Process -FilePath "ssh" `
    -ArgumentList "-o", "BatchMode=yes", "easten@192.168.100.165", $cmd2b `
    -RedirectStandardOutput $log2b `
    -RedirectStandardError "$log2b.err" `
    -PassThru -NoNewWindow

# --- Job 3: r06-5b, SSH to 165 ---
$cmd5b = "cd ~/dev/yixiaoguan-v2 && kimi --print -p .tasks/r06-5b-exec-dify-slim.md < /dev/null"
$p5b = Start-Process -FilePath "ssh" `
    -ArgumentList "-o", "BatchMode=yes", "easten@192.168.100.165", $cmd5b `
    -RedirectStandardOutput $log5b `
    -RedirectStandardError "$log5b.err" `
    -PassThru -NoNewWindow

# --- Save state ---
$state = [ordered]@{
    ts      = $ts
    started = (Get-Date -Format "o")
    jobs    = [ordered]@{
        "r06-4a" = @{ pid = $p4a.Id; log = $log4a; err = "$log4a.err" }
        "r06-2b" = @{ pid = $p2b.Id; log = $log2b; err = "$log2b.err" }
        "r06-5b" = @{ pid = $p5b.Id; log = $log5b; err = "$log5b.err" }
    }
}
$state | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 $statePath

Write-Host "=== Batch-3 dispatch launched ($ts) ==="
Write-Host "State file: $statePath"
Write-Host ""
Write-Host "  r06-4a  PID=$($p4a.Id)  log=$log4a"
Write-Host "  r06-2b  PID=$($p2b.Id)  log=$log2b"
Write-Host "  r06-5b  PID=$($p5b.Id)  log=$log5b"
Write-Host ""
Write-Host "Use  pwsh -File scripts\watch-batch-3.ps1  to poll progress."
