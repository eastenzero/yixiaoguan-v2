$ErrorActionPreference = 'SilentlyContinue'
$kbp = 'C:\Users\Administrator\Documents\code\kb-pipeline'
Write-Output "=== kb-pipeline 顶层目录 + 各自 KB-*.md 数 + 是否包含 frontmatter ==="
Get-ChildItem -Path $kbp -Directory | ForEach-Object {
    $cnt = (Get-ChildItem -Path $_.FullName -Filter 'KB-*.md' -Recurse | Measure-Object).Count
    Write-Output ("  {0,-40} KB-md={1}" -f $_.Name, $cnt)
}

Write-Output ""
Write-Output "=== 04-output 子目录 ==="
$out = "$kbp\04-output"
if (Test-Path $out) {
    Get-ChildItem -Path $out -Directory | ForEach-Object {
        $cnt = (Get-ChildItem -Path $_.FullName -Filter 'KB-*.md' -Recurse | Measure-Object).Count
        Write-Output ("  {0,-50} KB-md={1}" -f $_.FullName, $cnt)
    }
    $rootCnt = (Get-ChildItem -Path $out -Filter 'KB-*.md' -File | Measure-Object).Count
    Write-Output "  [04-output root] KB-md=$rootCnt"
}

Write-Output ""
Write-Output "=== 04-output 抽样 5 条文件名 ==="
Get-ChildItem -Path $out -Filter 'KB-*.md' -Recurse | Select-Object -First 5 | ForEach-Object { Write-Output ("  " + $_.FullName) }

Write-Output ""
Write-Output "=== 04-output 一条样本 frontmatter (head 30 行) ==="
$sample = Get-ChildItem -Path $out -Filter 'KB-*.md' -Recurse | Select-Object -First 1
if ($sample) {
    Get-Content -Path $sample.FullName -TotalCount 30 | ForEach-Object { Write-Output ("  " + $_) }
}

Write-Output ""
Write-Output "=== ai-ide-dumps-165 含义 ==="
$dump = "$kbp\ai-ide-dumps-165"
if (Test-Path $dump) {
    Get-ChildItem -Path $dump -Recurse -File | Select-Object -First 5 | ForEach-Object { Write-Output ("  " + $_.FullName.Substring($kbp.Length)) }
}

Write-Output ""
Write-Output "=== kb-pipeline 04-output 各文件夹按 status 字段统计（如果有 frontmatter）==="
$activeCnt = 0; $draftCnt = 0; $reviewCnt = 0; $noStatusCnt = 0
$files = Get-ChildItem -Path $out -Filter 'KB-*.md' -Recurse
$total = $files.Count
$i = 0
foreach ($f in $files) {
    $i++
    if ($i -gt 200) { break }  # only sample first 200
    $head = Get-Content -Path $f.FullName -TotalCount 25 -ErrorAction SilentlyContinue
    if ($head -match 'status:\s*"?active"?') { $activeCnt++ }
    elseif ($head -match 'status:\s*"?draft"?') { $draftCnt++ }
    elseif ($head -match 'status:\s*"?needs_review"?') { $reviewCnt++ }
    else { $noStatusCnt++ }
}
Write-Output ("  total scanned: {0} (out of {1})" -f $i, $total)
Write-Output ("  active: $activeCnt    draft: $draftCnt    needs_review: $reviewCnt    no-status: $noStatusCnt")

Write-Output ""
Write-Output "=== entries 866 vs kb-pipeline\04-output 比较 ==="
$entriesPath = 'C:\Users\Administrator\Documents\code\yixiaoguan\knowledge-base\entries'
$entryNames = Get-ChildItem -Path $entriesPath -Filter 'KB-*.md' -File | ForEach-Object { $_.Name }
$pipelineNames = Get-ChildItem -Path $out -Filter 'KB-*.md' -Recurse | ForEach-Object { $_.Name }
$entrySet = [System.Collections.Generic.HashSet[string]]::new([string[]]$entryNames)
$pipelineSet = [System.Collections.Generic.HashSet[string]]::new([string[]]$pipelineNames)
$intersect = [System.Collections.Generic.HashSet[string]]::new([string[]]$entryNames)
$intersect.IntersectWith($pipelineSet)
$onlyEntry = [System.Collections.Generic.HashSet[string]]::new([string[]]$entryNames)
$onlyEntry.ExceptWith($pipelineSet)
$onlyPipe = [System.Collections.Generic.HashSet[string]]::new([string[]]$pipelineNames)
$onlyPipe.ExceptWith($entrySet)
Write-Output ("  entries\* (root): {0} unique names" -f $entrySet.Count)
Write-Output ("  pipeline\04-output\**: {0} unique names" -f $pipelineSet.Count)
Write-Output ("  intersection: {0}" -f $intersect.Count)
Write-Output ("  only in entries: {0}" -f $onlyEntry.Count)
Write-Output ("  only in pipeline: {0}" -f $onlyPipe.Count)
