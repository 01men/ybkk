#!/usr/bin/env pwsh
# scripts/gates/gate.ps1 — 一键跑 5 道门禁（PowerShell 版本）
#
# 用法：
#   .\scripts\gates\gate.ps1 baseline   # 拍基线
#   .\scripts\gates\gate.ps1 all        # 跑 5 道门禁
#   .\scripts\gates\gate.ps1 status     # 看基线状态

[CmdletBinding()]
param([string]$Command = "all")

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir/../../..").Path

Set-Location $ProjectRoot

switch ($Command) {
    "baseline" {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "gate-baseline.ps1") -Snapshot
    }
    "status" {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "gate-baseline.ps1") -Status
    }
    "all" {
        $results = @()
        foreach ($g in @("gate-coverage", "gate-lint", "gate-deploy-test", "gate-e2e")) {
            $script = Join-Path $ScriptDir "$g.ps1"
            Write-Host ""
            Write-Host "[INFO] 跑 $g" -ForegroundColor Cyan
            & powershell -ExecutionPolicy Bypass -File $script
            $results += @{ gate = $g; code = $LASTEXITCODE }
        }
        Write-Host ""
        Write-Host "[INFO] 门禁汇总：" -ForegroundColor Cyan
        $failed = $false
        foreach ($r in $results) {
            $status = if ($r.code -eq 0) { "PASS" } else { "FAIL" }
            $color = if ($r.code -eq 0) { "Green" } else { "Red" }
            Write-Host "  $($r.gate): $status" -ForegroundColor $color
            if ($r.code -ne 0) { $failed = $true }
        }
        if ($failed) { exit 1 } else { exit 0 }
    }
    default {
        Write-Host "用法: gate.ps1 {baseline|all|status}"
        exit 1
    }
}