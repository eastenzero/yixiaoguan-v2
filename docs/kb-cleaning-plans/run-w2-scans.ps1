# W2 并行批量扫描执行器
# 用法：powershell -File run-w2-scans.ps1 [-Concurrency 20]
# 支持断点续传（已有报告的跳过）+ 失败自动重试一次

param(
    [int]$Concurrency = 20
)

$base = 'C:\Users\Administrator\Documents\code\kb-pipeline'
$taskDir = Join-Path $base 'kb-cleaning-plans\tasks'
$reportDir = Join-Path $base 'ws2-website-scrape\kimi-reports'

$allTasks = Get-ChildItem $taskDir -Filter 'w2-scan-*.md' | Sort-Object Name

# 筛选出需要执行的任务（跳过已有报告的）
$pendingTasks = @()
$skipped = 0
foreach ($task in $allTasks) {
    $safeName = $task.BaseName -replace '^w2-scan-', ''
    $report = Join-Path $reportDir "scan-$safeName.md"
    if (Test-Path $report) {
        $skipped++
    } else {
        $pendingTasks += $task
    }
}

$total = $allTasks.Count
$pending = $pendingTasks.Count

Write-Host "============================================="
Write-Host "W2 并行扫描（粗扫）"
Write-Host "总任务: $total / 已完成: $skipped / 待执行: $pending"
Write-Host "并发数: $Concurrency"
Write-Host "============================================="

if ($pending -eq 0) {
    Write-Host "全部已完成，无需执行。"
    exit 0
}

$startTime = Get-Date

# 分批执行
for ($batchStart = 0; $batchStart -lt $pending; $batchStart += $Concurrency) {
    $batchEnd = [Math]::Min($batchStart + $Concurrency, $pending)
    $batch = $pendingTasks[$batchStart..($batchEnd - 1)]
    $batchNum = [Math]::Floor($batchStart / $Concurrency) + 1
    $totalBatches = [Math]::Ceiling($pending / $Concurrency)
    
    Write-Host "`n--- 批次 $batchNum/$totalBatches（${batchStart}-${batchEnd} of $pending）---"
    
    $jobs = @()
    foreach ($task in $batch) {
        Write-Host "  启动: $($task.Name)"
        $job = Start-Job -ScriptBlock {
            param($base, $taskFile)
            & kimi --quiet -w $base -p $taskFile 2>&1 | Out-String
        } -ArgumentList $base, $task.FullName
        $jobs += @{ Job = $job; Task = $task }
    }
    
    # 等待本批完成（每批最多 10 分钟）
    $jobs.Job | Wait-Job -Timeout 600 | Out-Null
    
    # 检查结果
    $batchOk = 0; $batchFail = 0; $retryList = @()
    foreach ($item in $jobs) {
        $state = $item.Job.State
        if ($state -eq 'Running') { Stop-Job $item.Job }
        $null = Receive-Job $item.Job
        
        $safeName = $item.Task.BaseName -replace '^w2-scan-', ''
        $report = Join-Path $reportDir "scan-$safeName.md"
        if (Test-Path $report) {
            $batchOk++
            Write-Host "  OK: $safeName"
        } else {
            $batchFail++
            $retryList += $item.Task
            Write-Host "  FAIL: $safeName（将重试）"
        }
    }
    $jobs.Job | Remove-Job -Force
    
    # 失败的重试一次（串行）
    foreach ($task in $retryList) {
        Write-Host "  重试: $($task.Name)"
        & kimi --quiet -w $base -p $task.FullName 2>&1 | Out-Null
        $safeName = $task.BaseName -replace '^w2-scan-', ''
        $report = Join-Path $reportDir "scan-$safeName.md"
        if (Test-Path $report) {
            $batchOk++; $batchFail--
            Write-Host "  重试成功: $safeName"
        } else {
            Write-Host "  重试失败: $safeName"
        }
    }
    
    Write-Host "  批次结果: 成功 $batchOk / 失败 $batchFail"
}

$elapsed = ((Get-Date) - $startTime).TotalSeconds

# 最终统计
$finalReports = (Get-ChildItem $reportDir -Filter 'scan-*.md').Count
Write-Host "`n============================================="
Write-Host "完成！总耗时 $([math]::Round($elapsed))s"
Write-Host "报告总数: $finalReports / $total"
Write-Host "报告目录: $reportDir"
Write-Host "============================================="
