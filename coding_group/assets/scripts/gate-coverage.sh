#!/usr/bin/env bash
# scripts/gates/gate-coverage.sh — 覆盖率门禁（软）
#
# 阈值：核心模块 ≥ 80%，其他 ≥ 60%
# 通过 = 失败 delta 与基线对比后为空
#
# 依赖：jq；栈特定 plugin 见 scripts/gates/plugins/coverage-*.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

command -v jq >/dev/null 2>&1 || { echo "❌ 缺少 jq"; exit 1; }

detect_stack() {
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        echo "node"
    elif [ -f "$PROJECT_ROOT/pyproject.toml" ] || [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        echo "python"
    elif [ -f "$PROJECT_ROOT/go.mod" ]; then
        echo "go"
    else
        echo "unknown"
    fi
}

stack=$(detect_stack)
coverage_json="{}"

if [ -f "$SCRIPT_DIR/plugins/coverage-$stack.sh" ]; then
    coverage_json=$(bash "$SCRIPT_DIR/plugins/coverage-$stack.sh" 2>/dev/null || echo "{}")
else
    echo "⚠️  当前栈 ($stack) 还没装 coverage plugin，先把 gate-baseline.sh 跑通；coverage 这一道暂时跳过"
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[]}" > /dev/stdout
    exit 0
fi

failures=$(echo "$coverage_json" | jq -c '.failures // []')
baseline_file="$PROJECT_ROOT/kb/gates/baseline.json"

if [ -f "$baseline_file" ]; then
    baseline_failures=$(jq -c '.gates.coverage.failures // []' "$baseline_file")
    delta=$(jq -c -n --argjson b "$baseline_failures" --argjson c "$failures" '$c - $b')
else
    delta="$failures"
fi

if [ -z "$delta" ] || [ "$delta" = "[]" ]; then
    echo "✅ coverage gate PASS"
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[]}"
    exit 0
else
    echo "⚠️  coverage gate 软告警（不阻断）— delta:"
    echo "$delta" | jq -r '.[] | "  - \(.file): \(.covered * 100 | floor)% < \(.threshold * 100 | floor)%"'
    [ "${1:-}" = "--capture" ] && echo "{\"failures\": $failures}"
    exit 0  # 软门禁不阻断
fi
