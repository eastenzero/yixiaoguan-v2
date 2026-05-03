$ErrorActionPreference = 'Stop'
$work = "$PSScriptRoot"
$srcV1 = "$work\src-v1"
$srcV2 = "$work\src-v2"
New-Item -ItemType Directory -Force -Path $srcV1 | Out-Null
New-Item -ItemType Directory -Force -Path $srcV2 | Out-Null

# v1: only entries\KB-*.md root level files (excl. SUMMARY and first-batch-drafts)
$v1Source = 'C:\Users\Administrator\Documents\code\yixiaoguan\knowledge-base\entries'
$v1Files = Get-ChildItem -Path $v1Source -Filter 'KB-*.md' -File | Where-Object { $_.Name -notlike '*SUMMARY*' }
Write-Output "v1 source files: $($v1Files.Count)"
$v1Files | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination "$srcV1\$($_.Name)" -Force
}

# v2: all .md from kb-pipeline\04-output\final-merged\ (recursive, preserve category subdir as prefix in filename)
$v2Source = 'C:\Users\Administrator\Documents\code\kb-pipeline\04-output\final-merged'
$v2Files = Get-ChildItem -Path $v2Source -Filter 'KB-*.md' -Recurse -File
Write-Output "v2 source files: $($v2Files.Count)"
foreach ($f in $v2Files) {
    # Use original name; conflicts unlikely (KB-V2-CXX-NNN unique)
    $rel = $f.FullName.Substring($v2Source.Length + 1)
    $cat = (Split-Path $rel -Parent)
    if ($cat) {
        $newName = "$cat`__$($f.Name)" -replace '\\', '_'
    } else {
        $newName = $f.Name
    }
    Copy-Item -Path $f.FullName -Destination "$srcV2\$newName" -Force
}

Write-Output ""
Write-Output "Final counts:"
Write-Output "  src-v1: $((Get-ChildItem -Path $srcV1 -Filter '*.md').Count)"
Write-Output "  src-v2: $((Get-ChildItem -Path $srcV2 -Filter '*.md').Count)"
