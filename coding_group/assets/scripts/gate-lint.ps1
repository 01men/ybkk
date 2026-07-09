#!/usr/bin/env pwsh
# scripts/gates/gate-lint.ps1 — 静态扫描 + 安全扫描（PowerShell 版本，硬门禁）

[CmdletBinding()]
param([switch]$Capture)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir/../../..").Path

if (-not (Get-Command jq -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] 缺少 jq" -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot

$failures = @()

# 1. pnpm lint
if ((Test-Path "package.json") -and (Select-String -Path "package.json" -Pattern '"lint"' -Quiet)) {
    $logPath = "/tmp/lint-eslint.log"
    if (Test-Path $logPath) { Remove-Item $logPath -Force }
    & pnpm run lint --silent *> $logPath 2>&1
    if ($LASTEXITCODE -ne 0) {
        $errCount = (Select-String -Path $logPath -Pattern "error" -ErrorAction SilentlyContinue).Count ?? 0
        $failures += "lint:eslint-failed-$errCount"
    }
}

# 2. ruff（所有 Python 项目）
$pyprojs = Get-ChildItem -Path . -Filter pyproject.toml -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "node_modules" }
foreach ($pyproj in $pyprojs) {
    $projDir = Split-Path -Parent $pyproj.FullName
    Push-Location $projDir
    if (Get-Command ruff -ErrorAction SilentlyContinue) {
        $logPath = "/tmp/lint-ruff.log"
        if (Test-Path $logPath) { Remove-Item $logPath -Force }
        & ruff check src tests *> $logPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            $failures += "lint:ruff-failed-at-$projDir"
        }
    }
    Pop-Location
}

# 3. 敏感信息扫描
$secretHit = & git ls-files 2>$null |
    Where-Object { $_ -notmatch "node_modules" -and $_ -notmatch "coding_group" -and $_ -notmatch "\.lock$" -and $_ -notmatch "/tests/" } |
    ForEach-Object { Select-String -Path $_ -Pattern '(api[_-]?key|secret[_-]?key|password|access[_-]?token)\s*=\s*["\x27][^"\x27]+' -ErrorAction SilentlyContinue } |
    Select-Object -First 1
if ($secretHit) {
    $failures += "lint:secret-in-code:$($secretHit.Path)"
}

# 4. SQL 拼接扫描
$sqlHit = & git ls-files '*.py' '*.ts' '*.tsx' '*.go' 2>$null |
    ForEach-Object { Select-String -Path $_ -Pattern 'execute\(f["\x27]|execute\([^,)]*%[sd]' -ErrorAction SilentlyContinue } |
    Select-Object -First 1
if ($sqlHit) {
    $failures += "lint:sql-injection-risk:$($sqlHit.Path)"
}

$failuresJson = $failures | ConvertTo-Json -Compress
if (-not $failuresJson) { $failuresJson = "[]" }

$baselineFile = "coding_group/kb/gates/baseline.json"
$delta = $failuresJson

if (Test-Path $baselineFile) {
    $baselineFails = (Get-Content $baselineFile -Raw | ConvertFrom-Json).gates.lint.failures
    if ($null -eq $baselineFails) { $baselineFails = @() }
    # 简化版：直接当 JSON 字符串做差集比较
    $deltaJson = & jq -c -n --argjson b ($baselineFails | ConvertTo-Json -Compress) --argjson c $failuresJson '$c - $b'
} else {
    $deltaJson = $failuresJson
}

$deltaEmpty = ($deltaJson -eq "[]" -or [string]::IsNullOrEmpty($deltaJson))
if ($deltaEmpty) {
    Write-Host "[OK] lint gate PASS" -ForegroundColor Green
    if ($Capture) { '{"failures":[]}' }
    exit 0
} else {
    Write-Host "[ERROR] lint gate FAIL (硬门禁)" -ForegroundColor Red
    if ($Capture) { "{`"failures`":$failuresJson}" }
    exit 1
}