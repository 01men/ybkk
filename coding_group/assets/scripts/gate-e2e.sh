#!/usr/bin/env bash
# scripts/gates/gate-e2e.sh — E2E 测试（硬门禁）
#
# 默认 Playwright；Cypress 备选

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

command -v jq >/dev/null 2>&1 || { echo "❌ 缺少 jq"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ 缺少 node"; exit 1; }

cd "$PROJECT_ROOT"
mkdir -p .gate-output

RAW_OUTPUT=".gate-output/e2e-raw.json"

if [ -d "tests/e2e" ] && [ -f "playwright.config.ts" ]; then
    npx playwright test \
        --reporter=json \
        --output-dir="$PWD/.gate-output/playwright" \
        > "$RAW_OUTPUT" 2>&1 || true
elif [ -f "cypress.config.js" ] || [ -f "cypress.config.ts" ]; then
    npx cypress run --reporter=json > "$RAW_OUTPUT" 2>&1 || true
elif [ -d "tests/e2e" ] && find . -name "pyproject.toml" -path "*/tests/*" 2>/dev/null | head -1; then
    # Python E2E（pytest）
    if command -v pytest >/dev/null 2>&1; then
        uv run pytest tests/e2e -v --tb=short -q > "$RAW_OUTPUT" 2>&1 || true
    fi
else
    echo "❌ e2e gate FAIL: 没找到 Playwright / Cypress / pytest 配置"
    exit 1
fi

# 解析结果（兼容 Playwright JSON 报告）
failures=$(node <<'NODE'
const fs = require('fs');
let raw;
try {
    raw = fs.readFileSync('.gate-output/e2e-raw.json', 'utf8');
} catch (e) {
    console.log('[]');
    process.exit(0);
}
let data;
try { data = JSON.parse(raw); } catch (e) {
    // 可能是 pytest 输出：解析 ok/failed 行
    const failed = [];
    const lines = raw.split('\n');
    let currentTest = null;
    for (const line of lines) {
        const m = line.match(/^(.+?) (PASSED|FAILED|ERROR)$/);
        if (m) currentTest = m[1];
        if (line.includes('FAILED') && currentTest) {
            failed.push({ test: currentTest });
            currentTest = null;
        }
    }
    console.log(JSON.stringify({ failures: failed }));
    process.exit(0);
}
const failed = [];
if (Array.isArray(data.suites)) {
    for (const suite of data.suites) {
        for (const spec of (suite.specs || [])) {
            const title = spec.title || spec.specName || 'unknown';
            if (spec.ok === false) {
                failed.push({ test: title });
            } else if (Array.isArray(spec.tests)) {
                for (const t of spec.tests) {
                    const r = (t.results || [])[0];
                    if (r && r.status && r.status !== 'expected' && r.status !== 'passed') {
                        failed.push({ test: title });
                    }
                }
            }
        }
    }
}
console.log(JSON.stringify({ failures: failed }));
NODE
)

baseline_file="coding_group/kb/gates/baseline.json"
if [ -f "$baseline_file" ]; then
    baseline_fails=$(jq -c '.gates.e2e.failures // []' "$baseline_file")
    delta=$(jq -c -n --argjson b "$baseline_fails" --argjson c "$failures" '$c - $b')
else
    delta="$failures"
fi

if [ -z "$delta" ] || [ "$delta" = "[]" ]; then
    echo "✅ e2e gate PASS"
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[]}"
    exit 0
else
    echo "❌ e2e gate FAIL (硬门禁) — delta:"
    echo "$delta" | jq -r '.[] | "  - " + (.test // .)'
    [ "${1:-}" = "--capture" ] && echo "{\"failures\": $failures}"
    exit 1
fi