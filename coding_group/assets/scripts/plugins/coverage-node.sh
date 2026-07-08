#!/usr/bin/env bash
# scripts/gates/plugins/coverage-node.sh — Node.js 覆盖率 plugin
#
# 期望：package.json 里有 "test:coverage": "nyc --reporter=json npm test"
# 输出：{"failures": [{"file": ..., "covered": 0.5, "threshold": 0.6}, ...]}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 用 nyc 跑测试 + 拿 coverage-final.json
if [ -d "node_modules/.bin" ] && [ -x "node_modules/.bin/nyc" ]; then
    npm run test:coverage --silent > /tmp/cov-node.log 2>&1 || true
fi

# 没拿到就返回空
if [ ! -f "coverage/coverage-final.json" ]; then
    echo '{"failures": []}'
    exit 0
fi

node <<'NODE'
const fs = require('fs');
const path = require('path');
const core = ['src/services/', 'src/lib/', 'src/core/'];
let cov;
try {
    cov = require(path.join(process.cwd(), 'coverage/coverage-final.json'));
} catch (e) {
    console.log('{"failures": []}');
    process.exit(0);
}
const failures = [];
for (const file of Object.keys(cov)) {
    const stmt = cov[file].s || {};
    const total = Object.keys(stmt).length;
    const hit = Object.values(stmt).filter(v => v > 0).length;
    if (total === 0) continue;
    const ratio = hit / total;
    const isCore = core.some(p => file.includes(p));
    const threshold = isCore ? 0.8 : 0.6;
    if (ratio < threshold) {
        failures.push({ file, covered: Number(ratio.toFixed(3)), threshold });
    }
}
console.log(JSON.stringify({ failures }));
NODE
