# watch-batch-3.ps1
# Sleep for N seconds, then report on the 3 batch-3 jobs (pid alive + log tail).
# Exits early with AllDone = $true when all 3 jobs are done.
param(
    [int]$SleepSeconds = 180,
    [int]$TailLines   = 5
)

$ErrorActionPreference = "Stop"

$root      = "C:\Users\Administrator\Documents\code\yixiaoguan-v2"
$logDir    = Join-Path $root ".tasks\logs"
$statePath = Join-Path $logDir "batch-3-state.json"

if (-not (Test-Path $statePath)) {
    Write-Host "!! State file not found: $statePath"
    exit 2
}

Write-Host ">>> Waiting $SleepSeconds seconds before check... ($(Get-Date -Format HH:mm:ss))"
Start-Sleep -Seconds $SleepSeconds

$state = Get-Content $statePath -Raw | ConvertFrom-Json
$now   = Get-Date -Format "HH:mm:ss"
Write-Host ""
Write-Host "[$now] === Progress check (started at $($state.started)) ==="

$allDone = $true
foreach ($name in @("r06-4a", "r06-2b", "r06-5b")) {
    $j   = $state.jobs.$name
    $procPid = [int]$j.pid
    $log = $j.log
    $err = $j.err

    $running = $false
    $p = Get-Process -Id $procPid -ErrorAction SilentlyContinue
    if ($p) { $running = $true }

    $status   = if ($running) { "RUNNING" } else { "DONE   " }
    $logSize  = if (Test-Path $log) { (Get-Item $log).Length } else { 0 }
    $errSize  = if (Test-Path $err) { (Get-Item $err).Length } else { 0 }

    if ($running) { $allDone = $false }

    Write-Host ""
    Write-Host ("  [{0}] {1}  pid={2}  stdout={3}B  stderr={4}B" -f $status, $name, $procPid, $logSize, $errSize)

    if (Test-Path $log) {
        $tail = Get-Content $log -Tail $TailLines -ErrorAction SilentlyContinue
        if ($tail) {
            Write-Host "    --- last $TailLines lines of stdout ---"
            $tail | ForEach-Object { Write-Host "    | $_" }
        }
    }
    if ((Test-Path $err) -and $errSize -gt 0) {
        $etail = Get-Content $err -Tail 3 -ErrorAction SilentlyContinue
        if ($etail) {
            Write-Host "    --- last 3 lines of stderr ---"
            $etail | ForEach-Object { Write-Host "    ! $_" }
        }
    }
}

Write-Host ""
if ($allDone) {
    Write-Host "============================================"
    Write-Host "!!! ALL DONE — 3 jobs finished !!!"
    Write-Host "============================================"
    exit 0
} else {
    Write-Host "=== Still waiting; re-run watcher to poll again ==="
    exit 3
}
