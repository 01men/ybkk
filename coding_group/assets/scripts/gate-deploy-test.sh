#!/usr/bin/env bash
# scripts/gates/gate-deploy-test.sh — 部署 staging + 健康检查（硬门禁）
#
# 元冰可可 AIOS 用私有化部署：检测 deploy/compose/docker-compose.yml 是否能拉起

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

command -v jq >/dev/null 2>&1 || { echo "❌ 缺少 jq"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "❌ 缺少 curl"; exit 1; }

cd "$PROJECT_ROOT"

# ===== 私有化部署模式 ============================
# 元冰可可 AIOS 是私有化部署：deploy-test = 验证 docker-compose 可拉起 + 健康检查
DEPLOY_URL=""

if [ -f "deploy/compose/docker-compose.yml" ]; then
    # 私有化模式：检查 docker-compose config 可解析
    if command -v docker >/dev/null 2>&1; then
        if ! docker compose -f deploy/compose/docker-compose.yml config > /dev/null 2>&1; then
            echo "❌ deploy-test gate FAIL: docker-compose config 解析失败"
            [ "${1:-}" = "--capture" ] && echo '{"failures":["deploy-compose-invalid"]}'
            exit 1
        fi

        # 如果 install.sh 已经跑过（容器已起），做健康检查
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "aios_api_1"; then
            DEPLOY_URL="${AIOS_DEPLOY_TEST_URL:-http://localhost:8000}"
            if curl -sf "${DEPLOY_URL}/api/v1/health" > /dev/null; then
                echo "✅ deploy-test gate PASS — ${DEPLOY_URL}/api/v1/health"
                [ "${1:-}" = "--capture" ] && echo "{\"failures\":[], \"url\":\"${DEPLOY_URL}\"}"
                exit 0
            fi
        fi

        # 没起容器就 warn（CI 环境可能没装 Docker）
        echo "⚠️  deploy-test gate: docker-compose 配置 OK，但容器未启动"
        echo "   本地跑：cd deploy/compose && ./install.sh"
        [ "${1:-}" = "--capture" ] && echo '{"failures":["deploy-not-running"]}'
        exit 1
    fi
fi

# ===== 公有云兜底（其它项目可能用） ============================
if [ -f "vercel.json" ] || [ -f ".vercel/project.json" ]; then
    if command -v vercel >/dev/null 2>&1; then
        vercel_url=$(npx vercel --target=staging --confirm --token="${VERCEL_TOKEN:-}" 2>&1 \
            | grep -oE 'https://[a-zA-Z0-9.-]+\.vercel\.app' \
            | head -1 || true)
        DEPLOY_URL="$vercel_url"
    fi
fi

if [ -z "$DEPLOY_URL" ]; then
    echo "❌ deploy-test gate FAIL: 找不到部署平台"
    echo "   私有化：deploy/compose/docker-compose.yml 必须存在"
    echo "   公有云：在 vercel.json / wrangler.toml / fly.toml 中配一个"
    exit 1
fi

# ===== 等 readiness ============================
wait_for_health() {
    local url="$1"
    for i in {1..30}; do
        if curl -sf -o /dev/null "$url"; then return 0; fi
        sleep 2
    done
    return 1
}

if ! wait_for_health "$DEPLOY_URL"; then
    echo "❌ deploy-test gate FAIL: 健康检查 30 次都没过"
    [ "${1:-}" = "--capture" ] && echo '{"failures":["deploy-no-health"]}'
    exit 1
fi

echo "✅ deploy-test gate PASS — $DEPLOY_URL"
[ "${1:-}" = "--capture" ] && echo "{\"failures\":[], \"url\":\"$DEPLOY_URL\"}"
exit 0