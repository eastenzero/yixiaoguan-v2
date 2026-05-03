$ErrorActionPreference = 'Stop'
$work = "$PSScriptRoot\src-v2-flat"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force -Path $work | Out-Null

$src = 'C:\Users\Administrator\Documents\code\kb-pipeline\04-output\final-merged'
$files = Get-ChildItem -Path $src -Filter 'KB-*.md' -Recurse -File
foreach ($f in $files) {
    Copy-Item -Path $f.FullName -Destination (Join-Path $work $f.Name) -Force
}
Write-Output ("files: " + (Get-ChildItem -Path $work -Filter '*.md').Count)

Push-Location $PSScriptRoot
tar -czf v2-flat.tgz src-v2-flat
Pop-Location

$pkg = Get-Item "$PSScriptRoot\v2-flat.tgz"
Write-Output ("package: " + $pkg.FullName + "  " + $pkg.Length + " bytes")
