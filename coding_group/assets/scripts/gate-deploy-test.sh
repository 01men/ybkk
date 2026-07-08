#!/usr/bin/env bash
# scripts/gates/gate-deploy-test.sh — 部署 staging + 健康检查（硬门禁）
#
# 通用模板；你需要按你的部署平台改 detect_deploy_url()

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

command -v jq >/dev/null 2>&1 || { echo "❌ 缺少 jq"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "❌ 缺少 curl"; exit 1; }

cd "$PROJECT_ROOT"

# ===== 检测部署平台 ============================
DEPLOY_URL=""

if [ -f "vercel.json" ] || [ -f ".vercel/project.json" ]; then
    if command -v vercel >/dev/null 2>&1; then
        vercel_url=$(npx vercel --target=staging --confirm --token="${VERCEL_TOKEN:-}" 2>&1 \
            | grep -oE 'https://[a-zA-Z0-9.-]+\.vercel\.app' \
            | head -1 || true)
        DEPLOY_URL="$vercel_url"
    fi
elif [ -f "package.json" ] && grep -q '"deploy:staging"' package.json; then
    npm run deploy:staging > /tmp/deploy.log 2>&1 || true
    DEPLOY_URL=$(grep -oE 'https://[^ ]+' /tmp/deploy.log | head -1 || true)
elif [ -f "fly.toml" ]; then
    fly deploy --app "${FLY_APP_NAME:-myapp-staging}" > /tmp/deploy.log 2>&1 || true
    DEPLOY_URL="${STAGING_URL:-https://myapp-staging.fly.dev}"
elif [ -f "wrangler.toml" ]; then
    DEPLOY_URL="${CF_PAGES_URL:-https://staging.example.com}"
fi

if [ -z "$DEPLOY_URL" ]; then
    echo "❌ deploy-test gate FAIL: 找不到部署平台"
    echo "   请在 vercel.json / wrangler.toml / fly.toml / package.json 中配一个"
    echo "   或直接在脚本里写死 STAGING_URL"
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
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[\"deploy-no-health\"]}"
    exit 1
fi

if ! curl -sf -o /dev/null "$DEPLOY_URL"; then
    echo "❌ deploy-test gate FAIL: 主页返回非 200"
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[\"deploy-not-200\"]}"
    exit 1
fi

echo "✅ deploy-test gate PASS — $DEPLOY_URL"
[ "${1:-}" = "--capture" ] && echo "{\"failures\":[], \"url\":\"$DEPLOY_URL\"}"
exit 0
