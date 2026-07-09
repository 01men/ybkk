#!/usr/bin/env powershell
# scripts/gates/gate-baseline.ps1 — 基线管理（PowerShell 5.1 兼容版）
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File gate.ps1 baseline
#   powershell -ExecutionPolicy Bypass -File gate.ps1 status

[CmdletBinding()]
param(
    [switch]$Snapshot,
    [switch]$Status
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir/../../..").Path
$BaselineFile = Join-Path $ProjectRoot "coding_group/kb/gates/baseline.json"

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BaselineFile) | Out-Null

foreach ($cmd in @("jq", "git")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] missing dep: $cmd" -ForegroundColor Red
        exit 1
    }
}

function Run-Gate {
    param([string]$GateName, [string]$OutFile)
    $script = Join-Path $ScriptDir "$GateName.ps1"
    if (Test-Path $script) {
        $output = & powershell -ExecutionPolicy Bypass -File $script -Capture 2>&1
        $output | Out-File -FilePath $OutFile -Encoding UTF8
    }
}

if ($Snapshot) {
    Write-Host "[INFO] running all gates, capturing baseline..." -ForegroundColor Cyan
    $tmpDir = Join-Path $ProjectRoot ".gate-output"
    New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

    Run-Gate "gate-coverage" (Join-Path $tmpDir "coverage.json")
    Run-Gate "gate-lint" (Join-Path $tmpDir "lint.json")
    Run-Gate "gate-deploy-test" (Join-Path $tmpDir "deploy-test.json")
    Run-Gate "gate-e2e" (Join-Path $tmpDir "e2e.json")

    $capturedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss+00:00")
    $commitSha = & git -C $ProjectRoot rev-parse HEAD 2>$null
    if (-not $commitSha) { $commitSha = "unknown" }

    $coverageRaw = Get-Content (Join-Path $tmpDir "coverage.json") -Raw
    $lintRaw = Get-Content (Join-Path $tmpDir "lint.json") -Raw
    $deployTestRaw = Get-Content (Join-Path $tmpDir "deploy-test.json") -Raw
    $e2eRaw = Get-Content (Join-Path $tmpDir "e2e.json") -Raw

    $baseline = @{
        captured_at = $capturedAt
        commit_sha = $commitSha
        gates = @{
            coverage = $coverageRaw | ConvertFrom-Json
            lint = $lintRaw | ConvertFrom-Json
            "deploy-test" = $deployTestRaw | ConvertFrom-Json
            e2e = $e2eRaw | ConvertFrom-Json
        }
    }
    $baseline | ConvertTo-Json -Depth 10 | Out-File $BaselineFile -Encoding UTF8
    Write-Host "[OK] wrote baseline to $BaselineFile" -ForegroundColor Green
}

if ($Status) {
    if (-not (Test-Path $BaselineFile)) {
        Write-Host "[WARN] no baseline yet, run: gate.ps1 baseline" -ForegroundColor Yellow
        exit 2
    }
    Write-Host "[INFO] baseline status:" -ForegroundColor Cyan
    $baseline = Get-Content $BaselineFile -Raw | ConvertFrom-Json
    foreach ($gateName in @("coverage", "lint", "deploy-test", "e2e")) {
        $g = $baseline.gates.$gateName
        $count = 0
        if ($g.failures) { $count = @($g.failures).Count }
        Write-Host "  ${gateName}: $count recorded failures"
    }
}

if (-not ($Snapshot -or $Status)) { Show-Status }