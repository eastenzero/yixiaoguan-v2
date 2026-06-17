param(
  [switch]$SkipCleanCheck,
  [switch]$SkipTypeCheck,
  [switch]$SkipFetch
)

$ErrorActionPreference = 'Stop'

function Step($Message) {
  Write-Host "== $Message ==" -ForegroundColor Cyan
}

function Fail($Message) {
  Write-Host "ERROR: $Message" -ForegroundColor Red
  exit 1
}

$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
  Fail 'This script must be run inside a Git repository.'
}

Set-Location $repoRoot

Step 'Repository'
$branch = git branch --show-current
$head = git rev-parse --short HEAD
Write-Host "Branch: $branch"
Write-Host "HEAD:   $head"

if (-not $SkipFetch) {
  Step 'Fetch remotes'
  git fetch --all --prune
}

Step 'Upstream status'
$upstream = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
if ($upstream) {
  $counts = git rev-list --left-right --count "$upstream...HEAD"
  $parts = $counts -split '\s+'
  $behind = [int]$parts[0]
  $ahead = [int]$parts[1]
  Write-Host "Upstream: $upstream"
  Write-Host "Ahead:    $ahead"
  Write-Host "Behind:   $behind"
  if ($behind -gt 0) {
    Fail "Local branch is behind $upstream. Pull/rebase before release."
  }
} else {
  Write-Host 'No upstream configured; skipping ahead/behind gate.' -ForegroundColor Yellow
}

if (-not $SkipCleanCheck) {
  Step 'Clean worktree gate'
  $status = git status --porcelain=v1 --untracked-files=all
  if ($status) {
    Write-Host $status
    Fail 'Working tree is not clean. Commit, stash, or intentionally discard changes before release.'
  }
}

Step 'Whitespace gate'
git diff --check
git diff --cached --check

if (-not $SkipTypeCheck) {
  Step 'Student app type-check'
  Push-Location 'apps/student-app'
  npm run type-check
  Pop-Location

  Step 'Teacher app type-check'
  Push-Location 'apps/teacher-app'
  npm run type-check
  Pop-Location
}

Write-Host 'Pre-release checks passed.' -ForegroundColor Green
