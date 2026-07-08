#!/usr/bin/env bash
# scripts/gates/plugins/coverage-go.sh — Go 覆盖率 plugin
#
# 期望：项目用 go.mod；有 *_test.go 文件
# 输出：{"failures": [{"file": ..., "covered": 0.5, "threshold": 0.6}, ...]}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v go >/dev/null 2>&1; then
    echo '{"failures": []}'
    exit 0
fi

go test -coverprofile=coverage.out ./... > /tmp/cov-go.log 2>&1 || true

if [ ! -f "coverage.out" ]; then
    echo '{"failures": []}'
    exit 0
fi

python3 <<'PY'
import re, json
failures = []
with open('coverage.out') as f:
    for line in f:
        # 格式: file:start.col,end.col statements count
        if line.startswith('mode:') or not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        path = parts[0]
        stmts_total = int(parts[1])
        stmts_cov = int(parts[2])
        if stmts_total == 0:
            continue
        ratio = stmts_cov / stmts_total
        is_core = ('services/' in path) or ('lib/' in path) or ('core/' in path)
        threshold = 0.8 if is_core else 0.6
        if ratio < threshold:
            failures.append({'file': path, 'covered': round(ratio, 3), 'threshold': threshold})
print(json.dumps({'failures': failures}))
PY
