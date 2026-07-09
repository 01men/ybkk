#!/usr/bin/env pwsh
# scripts/gates/gate-deploy-test.ps1 — 部署测试（PowerShell 版本）
#
# 元冰可可 AIOS 是私有化部署：检测 deploy/compose/docker-compose.yml 能否拉起

[CmdletBinding()]
param([switch]$Capture)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir/../../..").Path

if (-not (Get-Command jq -ErrorAction SilentlyContinue)) { Write-Host "[ERROR] 缺少 jq" -ForegroundColor Red; exit 1 }
if (-not (Get-Command curl -ErrorAction SilentlyContinue)) { Write-Host "[ERROR] 缺少 curl" -ForegroundColor Red; exit 1 }

Set-Location $ProjectRoot

$composeFile = "deploy/compose/docker-compose.yml"
if (Test-Path $composeFile) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        # 私有化模式：检查 docker-compose config 可解析
        $dockerCheck = & docker compose -f $composeFile config 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] deploy-test gate FAIL: docker-compose config 解析失败" -ForegroundColor Red
            if ($Capture) { '{"failures":["deploy-compose-invalid"]}' }
            exit 1
        }

        # 如果容器已起，做健康检查
        $running = & docker ps --format '{{.Names}}' 2>$null | Select-String "aios_api_1"
        if ($running) {
            $deployUrl = if ($env:AIOS_DEPLOY_TEST_URL) { $env:AIOS_DEPLOY_TEST_URL } else { "http://localhost:8000" }
            try {
                & curl -sf "$deployUrl/api/v1/health" *> $null
                Write-Host "[OK] deploy-test gate PASS — $deployUrl/api/v1/health" -ForegroundColor Green
                if ($Capture) { "{`"failures`":[], `"url`":`"$deployUrl`"}" }
                exit 0
            } catch {
                Write-Host "[ERROR] deploy-test gate FAIL: 健康检查失败" -ForegroundColor Red
                if ($Capture) { '{"failures":["deploy-no-health"]}' }
                exit 1
            }
        }

        Write-Host "[WARN] deploy-test gate: docker-compose 配置 OK，但容器未启动" -ForegroundColor Yellow
        Write-Host "   本地跑：cd deploy/compose; .\install.ps1"
        if ($Capture) { '{"failures":["deploy-not-running"]}' }
        exit 1
    }
}

Write-Host "[ERROR] deploy-test gate FAIL: 找不到部署平台（私有化需要 docker）" -ForegroundColor Red
exit 1