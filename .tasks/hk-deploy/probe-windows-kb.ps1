$ErrorActionPreference = 'SilentlyContinue'
$base = 'C:\Users\Administrator\Documents\code'

$dirs = @(
    "$base\yixiaoguan",
    "$base\yixiaoguan\knowledge-base",
    "$base\yixiaoguan\knowledge-base\entries",
    "$base\yixiaoguan\wechat-articles",
    "$base\yixiaoguan\wechat-exports",
    "$base\yixiaoguan\wechat-exports-full",
    "$base\yixiaoguan\wechat-meta",
    "$base\yixiaoguan\data",
    "$base\yixiaoguan\kb-pipeline",
    "$base\yixiaoguan-v2",
    "$base\yixiaoguan-v2\knowledge-base",
    "$base\kb-pipeline",
    "$base\hermes-pipeline",
    "$base\yiguan-zhishu-proposal"
)

foreach ($d in $dirs) {
    if (Test-Path $d) {
        $totalMd = (Get-ChildItem -Path $d -Filter '*.md' -Recurse | Measure-Object).Count
        $kbMd    = (Get-ChildItem -Path $d -Filter 'KB-*.md' -Recurse | Measure-Object).Count
        $allFiles= (Get-ChildItem -Path $d -Recurse -File | Measure-Object).Count
        Write-Output ("{0,-72} all={1,-6} md={2,-6} KB-md={3}" -f $d, $allFiles, $totalMd, $kbMd)
    } else {
        Write-Output ("{0,-72} (NOT EXIST)" -f $d)
    }
}

Write-Output ""
Write-Output "=== yixiaoguan/knowledge-base/entries 子目录分布 ==="
$entries = "$base\yixiaoguan\knowledge-base\entries"
if (Test-Path $entries) {
    Get-ChildItem -Path $entries -Directory | ForEach-Object {
        $cnt = (Get-ChildItem -Path $_.FullName -Filter '*.md' -Recurse | Measure-Object).Count
        Write-Output ("  {0,-50} {1} files" -f $_.Name, $cnt)
    }
    $rootMd = (Get-ChildItem -Path $entries -Filter 'KB-*.md' -File | Measure-Object).Count
    Write-Output "  [root level KB-*.md] $rootMd"
}

Write-Output ""
Write-Output "=== yixiaoguan/knowledge-base 顶层目录 ==="
if (Test-Path "$base\yixiaoguan\knowledge-base") {
    Get-ChildItem -Path "$base\yixiaoguan\knowledge-base" -Directory | ForEach-Object {
        $cnt = (Get-ChildItem -Path $_.FullName -Filter '*.md' -Recurse | Measure-Object).Count
        Write-Output ("  {0,-30} md files: {1}" -f $_.Name, $cnt)
    }
}

Write-Output ""
Write-Output "=== wechat-* 目录里的 .md 文件抽样 ==="
foreach ($wd in @("$base\yixiaoguan\wechat-articles", "$base\yixiaoguan\wechat-exports", "$base\yixiaoguan\wechat-exports-full")) {
    if (Test-Path $wd) {
        Write-Output "--- $wd ---"
        Get-ChildItem -Path $wd -Recurse -File | Select-Object -First 5 | ForEach-Object { Write-Output ("  " + $_.FullName) }
    }
}

Write-Output ""
Write-Output "=== kb-pipeline 主目录 ==="
foreach ($p in @("$base\kb-pipeline", "$base\yixiaoguan\kb-pipeline")) {
    if (Test-Path $p) {
        Write-Output "--- $p ---"
        Get-ChildItem -Path $p -Directory | Select-Object -First 10 | ForEach-Object { Write-Output ("  dir: " + $_.Name) }
    }
}
