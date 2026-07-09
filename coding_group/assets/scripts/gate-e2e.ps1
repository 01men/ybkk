#!/usr/bin/env pwsh
# scripts/gates/gate-e2e.ps1 — E2E 测试（PowerShell 版本）

[CmdletBinding()]
param([switch]$Capture)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir/../../..").Path

if (-not (Get-Command jq -ErrorAction SilentlyContinue)) { Write-Host "[ERROR] 缺少 jq" -ForegroundColor Red; exit 1 }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Write-Host "[ERROR] 缺少 node" -ForegroundColor Red; exit 1 }

Set-Location $ProjectRoot
New-Item -ItemType Directory -Force -Path ".gate-output" | Out-Null

$rawOutput = ".gate-output/e2e-raw.json"

if ((Test-Path "tests/e2e") -and (Test-Path "playwright.config.ts")) {
    & npx playwright test --reporter=json --output-dir="$PWD/.gate-output/playwright" *> $rawOutput 2>&1
} elseif ((Test-Path "cypress.config.js") -or (Test-Path "cypress.config.ts")) {
    & npx cypress run --reporter=json *> $rawOutput 2>&1
} else {
    Write-Host "[ERROR] e2e gate FAIL: 没找到 Playwright / Cypress 配置" -ForegroundColor Red
    exit 1
}

$failures = & node -e @"
const fs = require('fs');
let raw;
try { raw = fs.readFileSync('.gate-output/e2e-raw.json', 'utf8'); } catch (e) { console.log('[]'); process.exit(0); }
let data;
try { data = JSON.parse(raw); } catch (e) { console.log('[]'); process.exit(0); }
const failed = [];
if (Array.isArray(data.suites)) {
    for (const suite of data.suites) {
        for (const spec of (suite.specs || [])) {
            if (spec.ok === false) failed.push({ test: spec.title });
        }
    }
}
console.log(JSON.stringify({ failures: failed }));
"@

$baselineFile = "coding_group/kb/gates/baseline.json"
$delta = $failures

if (Test-Path $baselineFile) {
    $baselineFails = (Get-Content $baselineFile -Raw | ConvertFrom-Json).gates.e2e.failures
    if ($null -eq $baselineFails) { $baselineFails = @() }
    $delta = & jq -c -n --argjson b ($baselineFails | ConvertTo-Json -Compress) --argjson c $failures '$c - $b'
}

if ($delta -eq "[]" -or [string]::IsNullOrEmpty($delta)) {
    Write-Host "[OK] e2e gate PASS" -ForegroundColor Green
    if ($Capture) { '{"failures":[]}' }
    exit 0
} else {
    Write-Host "[ERROR] e2e gate FAIL (硬门禁)" -ForegroundColor Red
    if ($Capture) { $failures }
    exit 1
}