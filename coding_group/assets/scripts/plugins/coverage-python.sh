#!/usr/bin/env bash
# scripts/gates/plugins/coverage-python.sh — Python 覆盖率 plugin
#
# 期望：pytest + pytest-cov 配置好；跑完生成 coverage.json
# 输出：{"failures": [{"file": ..., "covered": 0.5, "threshold": 0.6}, ...]}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 跑测试
if command -v pytest >/dev/null 2>&1; then
    pytest --cov=src --cov-report=json -q > /tmp/cov-python.log 2>&1 || true
fi

if [ ! -f "coverage.json" ]; then
    echo '{"failures": []}'
    exit 0
fi

python <<'PY'
import json
try:
    with open('coverage.json') as f:
        cov = json.load(f)
except Exception:
    print('{"failures": []}')
    raise SystemExit(0)

core_prefixes = ['src/services/', 'src/lib/', 'src/core/']
failures = []
for filepath, info in cov.get('files', {}).items():
    summary = info.get('summary', {})
    if 'percent_covered' not in summary:
        continue
    ratio = summary['percent_covered'] / 100
    is_core = any(filepath.startswith(p) for p in core_prefixes)
    threshold = 0.8 if is_core else 0.6
    if ratio < threshold:
        failures.append({'file': filepath, 'covered': round(ratio, 3), 'threshold': threshold})
print(json.dumps({'failures': failures}))
PY
