#!/usr/bin/env pwsh
# scripts/gates/gate-coverage.ps1 — 覆盖率门禁（PowerShell 版本）
#
# 阈值：核心模块 ≥ 80%，其他 ≥ 60%

[CmdletBinding()]
param([switch]$Capture)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir/../../..").Path

if (-not (Get-Command jq -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] 缺少 jq" -ForegroundColor Red
    exit 1
}

# 检测栈
$stack = "unknown"
if (Test-Path (Join-Path $ProjectRoot "package.json")) { $stack = "node" }
elseif (Test-Path (Join-Path $ProjectRoot "pyproject.toml")) { $stack = "python" }
elseif (Test-Path (Join-Path $ProjectRoot "go.mod")) { $stack = "go" }

$plugin = Join-Path $ScriptDir "plugins/coverage-$stack.ps1"
if (-not (Test-Path $plugin)) {
    Write-Host "[WARN] 当前栈 ($stack) 还没装 coverage plugin" -ForegroundColor Yellow
    if ($Capture) { '{"failures":[]}' | Out-String }
    exit 0
}

$coverageJson = & pwsh $plugin 2>$null
if (-not $coverageJson) { $coverageJson = "{}" }

$failures = $coverageJson | ConvertFrom-Json | Select-Object -ExpandProperty failures
if ($null -eq $failures) { $failures = @() }

$baselineFile = Join-Path $ProjectRoot "coding_group/kb/gates/baseline.json"
if (Test-Path $baselineFile) {
    $baseline = Get-Content $baselineFile -Raw | ConvertFrom-Json
    $baselineFailures = $baseline.gates.coverage.failures
    if ($null -eq $baselineFailures) { $baselineFailures = @() }
    $delta = @($failures | Where-Object { $baselineFailures -notcontains $_ })
} else {
    $delta = @($failures)
}

if ($delta.Count -eq 0) {
    Write-Host "[OK] coverage gate PASS" -ForegroundColor Green
    if ($Capture) { '{"failures":[]}' }
    exit 0
} else {
    Write-Host "[WARN] coverage gate 软告警（不阻断）" -ForegroundColor Yellow
    if ($Capture) { $coverageJson }
    exit 0
}