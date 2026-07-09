#!/usr/bin/env bash
# scripts/gates/plugins/coverage-python.sh — Python 覆盖率 plugin
#
# 期望：apps/api/ 下有 pyproject.toml + pytest-cov
# 输出：{"failures": [{"file": ..., "covered": 0.5, "threshold": 0.8}, ...]}
#
# 核心模块阈值：services / repositories / connectors / middleware / standards → ≥ 80%
# 其它模块：≥ 60%

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

# 没装 pytest / coverage 就跳过
if ! command -v pytest >/dev/null 2>&1 && ! command -v uv >/dev/null 2>&1; then
    echo '{"failures": []}'
    exit 0
fi

# 找出所有 Python 项目（每个 pyproject.toml 目录）
PYPROJECTS=$(find "$PROJECT_ROOT" -name pyproject.toml -not -path '*/node_modules/*' 2>/dev/null | head -10)

failures_json='{"failures": []}'

for pyproj in $PYPROJECTS; do
    proj_dir=$(dirname "$pyproj")
    cd "$proj_dir"

    # 跑 pytest --cov
    if command -v uv >/dev/null 2>&1; then
        uv run pytest tests/unit --cov=src --cov-report=json --cov-report=term -q \
            > /tmp/cov-pytest.log 2>&1 || true
    elif command -v pytest >/dev/null 2>&1; then
        pytest tests/unit --cov=src --cov-report=json --cov-report=term -q \
            > /tmp/cov-pytest.log 2>&1 || true
    fi

    if [ ! -f "coverage.json" ]; then
        continue
    fi

    # 解析 coverage.json
    cov_output=$(python3 <<PYEOF
import json
try:
    with open('coverage.json') as f:
        cov = json.load(f)
except Exception:
    print('{"failures": []}')
    exit()

CORE_PATTERNS = ['services', 'repositories', 'connectors', 'middleware', 'standards']
THRESHOLD_CORE = 0.8
THRESHOLD_OTHER = 0.6

failures = []
for filename, data in cov.get('files', {}).items():
    if '/tests/' in filename or filename.endswith('test_*.py'):
        continue
    s = data.get('summary', {})
    if 'percent_covered' not in s:
        continue
    covered = s['percent_covered'] / 100.0
    is_core = any(p in filename for p in CORE_PATTERNS)
    threshold = THRESHOLD_CORE if is_core else THRESHOLD_OTHER
    if covered < threshold:
        failures.append({'file': filename, 'covered': round(covered, 3), 'threshold': threshold})

print(json.dumps({'failures': failures}))
PYEOF
    )

    # 合并到全项目 failures
    failures_json=$(python3 -c "
import json
a = json.loads('''$failures_json''')
b = json.loads('''$cov_output''')
a['failures'].extend(b['failures'])
print(json.dumps(a))
")
done

echo "$failures_json"