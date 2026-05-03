$ErrorActionPreference = 'SilentlyContinue'
$v1Entries = 'C:\Users\Administrator\Documents\code\yixiaoguan\knowledge-base\entries'
$v2Final   = 'C:\Users\Administrator\Documents\code\kb-pipeline\04-output\final-merged'
$v2Merged  = 'C:\Users\Administrator\Documents\code\kb-pipeline\04-output\merged'

Write-Output "=== final-merged 分类目录(按学院/主题) ==="
Get-ChildItem -Path $v2Final -Directory | ForEach-Object {
    $cnt = (Get-ChildItem -Path $_.FullName -Filter '*.md' -Recurse | Measure-Object).Count
    Write-Output ("  {0,-30} {1}" -f $_.Name, $cnt)
}

Write-Output ""
Write-Output "=== merged vs final-merged: 是否 final-merged 是 merged 的优化版 ==="
$mergedCount = (Get-ChildItem -Path $v2Merged -Filter 'KB-*.md' -Recurse | Measure-Object).Count
$finalCount  = (Get-ChildItem -Path $v2Final -Filter 'KB-*.md' -Recurse | Measure-Object).Count
Write-Output ("  merged total: $mergedCount")
Write-Output ("  final-merged total: $finalCount")

# 比对同名文件大小
$sample = Get-ChildItem -Path $v2Final -Filter 'KB-V2-C07-001.md' -Recurse | Select-Object -First 1
if ($sample) {
    $matchInMerged = Get-ChildItem -Path $v2Merged -Filter $sample.Name -Recurse | Select-Object -First 1
    if ($matchInMerged) {
        Write-Output ("  Same file '{0}' final={1}B  merged={2}B" -f $sample.Name, $sample.Length, $matchInMerged.Length)
    }
}

Write-Output ""
Write-Output "==================================================================================="
Write-Output "=== 主题对比: 5 个主题各取 1 条 v1 + 1 条 v2 final-merged 内容 ==="
Write-Output "==================================================================================="

$themes = @(
    @{ name = '校医院/医疗'; v1pattern = '*医*'; v2pattern = '医疗与心理\KB-V2-C07*' },
    @{ name = '奖学金/助学贷款'; v1pattern = '*奖学*'; v2pattern = '*奖助*\*' },
    @{ name = '宿舍/电费'; v1pattern = '*电费*'; v2pattern = '*宿舍*\*' },
    @{ name = '通勤车/班车'; v1pattern = '*通勤*'; v2pattern = '*' },
    @{ name = '心理咨询'; v1pattern = '*心理*'; v2pattern = '*心理*' }
)

foreach ($th in $themes) {
    Write-Output ""
    Write-Output ("------- [主题: {0}] -------" -f $th.name)
    
    $v1f = Get-ChildItem -Path $v1Entries -Filter $th.v1pattern -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($v1f) {
        Write-Output ("v1 entries: {0} ({1}B)" -f $v1f.Name, $v1f.Length)
        Write-Output "--- v1 内容 ---"
        Get-Content -Path $v1f.FullName -TotalCount 35 | ForEach-Object { Write-Output ("  " + $_) }
    } else {
        Write-Output "v1 entries: (no match)"
    }
    
    Write-Output ""
    $v2f = Get-ChildItem -Path $v2Final -Filter '*.md' -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like ('*' + $th.v2pattern) } | Select-Object -First 1
    if ($v2f) {
        Write-Output ("v2 final-merged: {0} ({1}B)" -f $v2f.FullName.Substring($v2Final.Length+1), $v2f.Length)
        Write-Output "--- v2 内容 ---"
        Get-Content -Path $v2f.FullName -TotalCount 35 | ForEach-Object { Write-Output ("  " + $_) }
    } else {
        Write-Output "v2 final-merged: (no match)"
    }
}

Write-Output ""
Write-Output "==================================================================================="
Write-Output "=== final-merged 抽样 5 条 (不同分类) ==="
Write-Output "==================================================================================="
Get-ChildItem -Path $v2Final -Directory | Get-Random -Count ([Math]::Min(5, (Get-ChildItem -Path $v2Final -Directory).Count)) | ForEach-Object {
    $rand = Get-ChildItem -Path $_.FullName -Filter 'KB-*.md' -File -ErrorAction SilentlyContinue | Get-Random -Count 1
    if ($rand) {
        Write-Output ("--- " + $_.Name + " :: " + $rand.Name + " ---")
        Get-Content -Path $rand.FullName -TotalCount 25 | ForEach-Object { Write-Output ("  " + $_) }
        Write-Output ""
    }
}
