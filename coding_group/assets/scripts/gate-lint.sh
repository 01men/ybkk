#!/usr/bin/env bash
# scripts/gates/gate-lint.sh — 静态扫描 + 安全扫描（硬门禁）
#
# 包含：
#   1. ESLint / Flake8 / golangci-lint
#   2. 敏感信息扫描（API key、密码、token 字面量）
#   3. SQL 拼接扫描
#   4. console.log / print() 警用

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

command -v jq >/dev/null 2>&1 || { echo "❌ 缺少 jq"; exit 1; }
cd "$PROJECT_ROOT"

failures=()

# 1. 跑项目自带 lint
if [ -f "package.json" ] && grep -q '"lint"' package.json; then
    if ! npm run lint --silent > /tmp/lint-eslint.log 2>&1; then
        failures+=("lint:eslint-failed-$(grep -c 'error' /tmp/lint-eslint.log || echo 0)")
    fi
fi
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    if command -v flake8 >/dev/null 2>&1; then
        if ! python -m flake8 src/ > /tmp/lint-flake8.log 2>&1; then
            failures+=("lint:flake8-failed")
        fi
    fi
fi
if [ -f "go.mod" ]; then
    if command -v golangci-lint >/dev/null 2>&1; then
        if ! golangci-lint run > /tmp/lint-go.log 2>&1; then
            failures+=("lint:golangci-failed")
        fi
    fi
fi

# 2. 敏感信息扫描
secret_hit=$(git ls-files 2>/dev/null \
    | xargs grep -lE '(api[_-]?key|secret[_-]?key|password|access[_-]?token)\s*=\s*["\x27][^"\x27]+' 2>/dev/null \
    | grep -v '\.env\.example$' \
    | grep -v '^scripts/gates/' \
    | head -1 || true)
[ -n "$secret_hit" ] && failures+=("lint:secret-in-code:$secret_hit")

# 3. SQL 拼接扫描
sql_hit=$(git ls-files '*.py' '*.ts' '*.tsx' '*.go' 2>/dev/null \
    | xargs grep -lE 'execute\(f["\x27]|execute\([^,)]*%[sd]|execute\([^,)]*\+[^,)]*\)' 2>/dev/null \
    | head -1 || true)
[ -n "$sql_hit" ] && failures+=("lint:sql-injection-risk:$sql_hit")

# 4. console.log / print 警用（项目用 logger 才不警）
logger_hit=$(git ls-files '*.ts' '*.tsx' 2>/dev/null \
    | xargs grep -lE 'console\.log\(' 2>/dev/null \
    | head -3 || true)
# 仅警告不进 failures（用 exclusions 文件控制）

# === 输出 ============================================
failures_json=$(printf '%s\n' "${failures[@]}" | jq -R . | jq -s 'map(select(. != ""))')

baseline_file="kb/gates/baseline.json"
if [ -f "$baseline_file" ]; then
    baseline_fails=$(jq -c '.gates.lint.failures // []' "$baseline_file")
    delta=$(jq -c -n --argjson b "$baseline_fails" --argjson c "$failures_json" '$c - $b')
else
    delta="$failures_json"
fi

if [ -z "$delta" ] || [ "$delta" = "[]" ]; then
    echo "✅ lint gate PASS"
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[]}"
    exit 0
else
    echo "❌ lint gate FAIL (硬门禁) — delta:"
    echo "$delta" | jq -r '.[] | "  - " + .'
    [ "${1:-}" = "--capture" ] && echo "{\"failures\": $failures_json}"
    exit 1
fi
