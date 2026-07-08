# 5 道门禁脚本：怎么写、怎么跑、怎么失败

> 这一章回答：5 道门禁脚本长什么样，怎么放在仓库里，谁触发它们，怎么看结果。

---

## 一、5 道门禁的硬 / 软配置

| # | 门禁脚本 | 类型 | 判定 | 在你这边怎么实现 |
|---|---|---|---|---|
| 1 | `gate-baseline.sh` | **元门禁** | 跑前先看基线 / 跑后做差集 | bash 主程序 + JSON diff |
| 2 | `gate-coverage.sh` | 软门禁 | 核心 ≥ 80%、其他 ≥ 60% | 跑 `nyc` / `pytest-cov` / `go test -cover` |
| 3 | `gate-lint.sh` | **硬门禁** | lint 通过 + 敏感信息扫描 + 拼 SQL 扫描 | ESLint / Flake8 / golangci-lint + 自定义 grep |
| 4 | `gate-deploy-test.sh` | **硬门禁** | staging 部署 + 健康检查 200 | bash 调 `vercel --prod --target=staging` + curl |
| 5 | `gate-e2e.sh` | **硬门禁** | 关键路径 E2E 全过 | 跑 `playwright test` / `cypress run` |

> 软门禁不阻断，但留「伤疤」。详见 `assets/skills/feedback-loop-rules/SKILL.md` §3。

---

## 二、基线对比机制（剥夺 AI 解释权的关键）

基线脚本生成的 `kb/gates/baseline.json` 长这样：

```json
{
  "captured_at": "2026-07-08T15:00:00+08:00",
  "commit_sha": "abc1234",
  "gates": {
    "coverage": {
      "status": "current",
      "failures": [
        {"file": "src/legacy/foo.ts", "covered": 0.45, "threshold": 0.6}
      ]
    },
    "lint": {
      "status": "current",
      "failures": []
    },
    "deploy-test": {
      "status": "current",
      "failures": []
    },
    "e2e": {
      "status": "current",
      "failures": []
    }
  }
}
```

**判定逻辑**（基线对比的算法）：

```bash
# 在每个 gate-*.sh 脚本里
new_failures=$(jq -r '.failures' "$gate_output_json")
baseline_failures=$(jq -r ".gates.${gate_name}.failures" "$baseline_json")

# 重要：把列表转成 sorted 的字符串再比较
delta=$(diff <(echo "$baseline_failures" | jq 'sort') \
            <(echo "$new_failures" | jq 'sort'))

if [ -z "$delta" ]; then
    echo "✅ $gate_name PASS"
    exit 0
else
    echo "❌ $gate_name FAIL — new failures:"
    echo "$delta"
    exit 1
fi
```

> 「历史问题」这把万能钥匙就这么没了——AI 没法再说「这不是我引入的」。

---

## 三、5 道门禁脚本的实现

### 3.1 `gate-baseline.sh`（核心，必须先写）

这一份给完整可用的实现：

```bash
#!/usr/bin/env bash
# scripts/gates/gate-baseline.sh — 基线管理：拍快照 / 比对 / 查状态
#
# 用法：
#   ./scripts/gates/gate-baseline.sh --snapshot   # 跑一遍所有门禁，写成基线
#   ./scripts/gates/gate-baseline.sh status         # 看基线状态
#   ./scripts/gates/gate-baseline.sh diff <gate>    # 看某门禁在 baseline 之后的差集

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BASELINE_FILE="$PROJECT_ROOT/kb/gates/baseline.json"
GATE_OUTPUT_DIR="$PROJECT_ROOT/.gate-output"

mkdir -p "$GATE_OUTPUT_DIR"
mkdir -p "$(dirname "$BASELINE_FILE")"

# 跑一次全部 5 道门禁，输出到 $GATE_OUTPUT_DIR
run_all_gates() {
    bash "$SCRIPT_DIR/gate-coverage.sh" --capture > "$GATE_OUTPUT_DIR/coverage.json" || true
    bash "$SCRIPT_DIR/gate-lint.sh" --capture > "$GATE_OUTPUT_DIR/lint.json" || true
    bash "$SCRIPT_DIR/gate-deploy-test.sh" --capture > "$GATE_OUTPUT_DIR/deploy-test.json" || true
    bash "$SCRIPT_DIR/gate-e2e.sh" --capture > "$GATE_OUTPUT_DIR/e2e.json" || true
}

snapshot() {
    echo "🔍 跑全部门禁，生成基线快照…"
    run_all_gates

    # 拼成 baseline.json
    cat > "$BASELINE_FILE" <<EOF
{
  "captured_at": "$(date -u +%FT%T+00:00)",
  "commit_sha": "$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "gates": {
    "coverage": $(cat "$GATE_OUTPUT_DIR/coverage.json"),
    "lint": $(cat "$GATE_OUTPUT_DIR/lint.json"),
    "deploy-test": $(cat "$GATE_OUTPUT_DIR/deploy-test.json"),
    "e2e": $(cat "$GATE_OUTPUT_DIR/e2e.json")
  }
}
EOF

    echo "✅ 已写入 $BASELINE_FILE"
}

status() {
    if [ ! -f "$BASELINE_FILE" ]; then
        echo "⚠️  还没有基线，跑一次 ./scripts/gates/gate-baseline.sh --snapshot"
        exit 2
    fi
    echo "📊 基线状态："
    jq -r '
      .gates | to_entries[] |
      "  " + .key + ": " + (.value.failures | length | tostring) + " 已记录失败"
    ' "$BASELINE_FILE"
}

case "${1:-status}" in
    --snapshot) snapshot ;;
    status) status ;;
    *) echo "用法: $0 [--snapshot|status|diff <gate>]"; exit 1 ;;
esac
```

放在 `scripts/gates/gate-baseline.sh`，加 `chmod +x`。

> 这一份**直接能用**，但其他 4 道门禁脚本需要按你的栈改造。下一节给框架。

---

### 3.2 `gate-coverage.sh`（框架 + 按栈 plugin）

主入口：

```bash
#!/usr/bin/env bash
# scripts/gates/gate-coverage.sh — 覆盖率门禁
#
# 用法：
#   ./scripts/gates/gate-coverage.sh         # 跑 + 判定通过/失败
#   ./scripts/gates/gate-coverage.sh --capture  # 跑 + 输出 failures JSON，退出码不管

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# === 栈特定检测（按你的项目改这里）========================
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

# === 调用栈特定 plugin 算出覆盖率 ===========================
coverage_json=$(bash "$SCRIPT_DIR/plugins/coverage-$(detect_stack).sh" 2>/dev/null || echo '{}')

# === 取出 failures 列表，做基线对比 =========================
failures=$(echo "$coverage_json" | jq -c '.failures // []')
baseline_file="$PROJECT_ROOT/kb/gates/baseline.json"

if [ -f "$baseline_file" ]; then
    baseline_failures=$(jq -c '.gates.coverage.failures // []' "$baseline_file")
    delta=$(jq -c --argjson b "$baseline_failures" --argjson c "$failures" \
        '$c - $b' <<< '{}' 2>/dev/null || echo '[]')
else
    delta="$failures"
fi

# === 判定 + 输出 ==========================================
if [ -z "$delta" ] || [ "$delta" = "[]" ]; then
    echo "✅ coverage gate PASS"
    [ "${1:-}" = "--capture" ] && echo "{\"failures\":[]}" > /dev/stdout
    exit 0
else
    echo "❌ coverage gate FAIL — delta:"
    echo "$delta" | jq -r '.[] | "  - \(.file): \(.covered) < \(.threshold)"'
    [ "${1:-}" = "--capture" ] && echo "{\"failures\": $failures}" > /dev/stdout
    # 软门禁：警告，但不阻断
    echo "⚠️  coverage 是软门禁，不阻断流程；建议关注"
    exit 0
fi
```

栈 plugin 示例（`scripts/gates/plugins/coverage-node.sh`）：

```bash
#!/usr/bin/env bash
# scripts/gates/plugins/coverage-node.sh — Node.js 覆盖率 plugin
#
# 用法：在你的 package.json 里加 "test:coverage": "nyc --reporter=json npm test"
# 输出 JSON：{"failures": [{"file": "...", "covered": 0.5, "threshold": 0.6}, ...]}

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 跑测试 + 拿 JSON
npm run test:coverage --silent > /tmp/cov.out 2>&1 || true

# nyc 的输出格式示例：
# {"src/foo.ts": {"s": {1: 1, 2: 0, ...}, "path": "src/foo.ts", "all": 100, "covered": 80}}
# 我们解析成 {failures: [{file, covered, threshold}, ...]}，threshold 核心 0.8 其他 0.6

node <<'NODE'
const fs = require('fs');
const path = require('path');
const core = ['src/services/', 'src/lib/'];
const cov = require(path.join(process.cwd(), 'coverage/coverage-final.json'));
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
        failures.push({ file, covered: ratio, threshold });
    }
}
console.log(JSON.stringify({ failures }));
NODE
```

Python plugin (`plugins/coverage-python.sh`)：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python <<'PY'
import json, subprocess, os, re
out = subprocess.run(['pytest', '--cov=src', '--cov-report=json', '-q'],
                     capture_output=True, text=True).stdout
# parse .coverage.json
import json as _j
with open('coverage.json') as f:
    cov = _j.load(f)
core_prefixes = ['src/services/', 'src/lib/']
failures = []
for f, v in cov['files'].items():
    ratio = v['summary']['percent_covered'] / 100
    is_core = any(f.startswith(p) for p in core_prefixes)
    threshold = 0.8 if is_core else 0.6
    if ratio < threshold:
        failures.append({'file': f, 'covered': round(ratio, 3), 'threshold': threshold})
print(json.dumps({'failures': failures}))
PY
```

Go plugin (`plugins/coverage-go.sh`)：

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

go test -coverprofile=coverage.out ./... > /dev/null 2>&1 || true
go tool cover -func=coverage.out | awk '
    /\.go:/ {
        match($0, /([0-9.]+)%/, m);
        file = $2;
        sub(/:.*/, "", file);
        pct = m[1] + 0;
        is_core = (file ~ /services\/|lib\//);
        threshold = is_core ? 80 : 60;
        if (pct < threshold) {
            print file, pct, threshold;
        }
    }
' | python3 -c '
import sys, json
fails = []
for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) >= 3:
        fails.append({"file": parts[0], "covered": float(parts[1])/100, "threshold": float(parts[2])/100})
print(json.dumps({"failures": fails}))
'
```

---

### 3.3 `gate-lint.sh`（硬门禁）

```bash
#!/usr/bin/env bash
# scripts/gates/gate-lint.sh — 静态扫描 + 安全扫描
#
# 包含：
#   1. ESLint / Flake8 / golangci-lint
#   2. 敏感信息扫描（API key、密码、token 字面量）
#   3. SQL 拼接扫描（直接拼字符串的 SQL）
#   4. console.log / print() 警用（项目用统一 logger）

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

failures=()

# 1. 跑项目自带 lint
if [ -f "package.json" ] && grep -q '"lint"' package.json; then
    npm run lint --silent || failures+=("lint:eslint-failed")
fi
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
    python -m flake8 src/ || failures+=("lint:flake8-failed")
fi
if [ -f "go.mod" ]; then
    golangci-lint run || failures+=("lint:golangci-failed")
fi

# 2. 敏感信息扫描
scan_secrets() {
    # 简化版：扫常见 API key 模式
    git ls-files | xargs grep -lE '(api[_-]?key|secret|password|token)\s*=\s*["\x27][^"\x27]+' 2>/dev/null \
        | grep -v '.env.example' \
        | grep -v 'scripts/gates/' \
        | head -1
}

secret_hit=$(scan_secrets || true)
[ -n "$secret_hit" ] && failures+=("lint:secret-in-code:$secret_hit")

# 3. SQL 拼接扫描
scan_sql_injection() {
    # 简化版：检测 .py 文件里有没有 f-string 拼 SQL 或者模板字符串
    git ls-files '*.py' '*.ts' '*.tsx' '*.go' 2>/dev/null \
        | xargs grep -lE 'execute\(f["\x27]|execute\([^,)]*%[sd]|execute\([^,)]*\+[^,)]*\)' 2>/dev/null \
        | head -1
}

sql_hit=$(scan_sql_injection || true)
[ -n "$sql_hit" ] && failures+=("lint:sql-injection-risk:$sql_hit")

# === 输出 + 判定 ====================
failures_json=$(printf '%s\n' "${failures[@]}" | jq -R . | jq -s 'map(select(. != ""))')

# 基线对比
baseline_file="kb/gates/baseline.json"
if [ -f "$baseline_file" ]; then
    baseline_fails=$(jq -c '.gates.lint.failures // []' "$baseline_file")
    delta=$(jq -c --argjson b "$baseline_fails" --argjson c "$failures_json" '$c - $b' <<< '{}' 2>/dev/null || echo '[]')
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
```

---

### 3.4 `gate-deploy-test.sh`（硬门禁）

```bash
#!/usr/bin/env bash
# scripts/gates/gate-deploy-test.sh — 部署 staging + 健康检查
#
# 通用版：deploy.sh 调部署平台命令；健康检查用 curl

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 1. 触发部署（按你的栈）
DEPLOY_URL=""

if [ -f "vercel.json" ]; then
    DEPLOY_URL=$(npx vercel --target=staging --confirm --token="$VERCEL_TOKEN" 2>/dev/null \
        | grep -oE 'https://[^ ]+' | head -1)
elif [ -f "package.json" ] && grep -q '"deploy:staging"' package.json; then
    npm run deploy:staging > /tmp/deploy.log 2>&1
    DEPLOY_URL=$(grep -oE 'https://[^ ]+' /tmp/deploy.log | head -1)
elif [ -f "fly.toml" ]; then
    fly deploy --app myapp-staging > /tmp/deploy.log 2>&1
    DEPLOY_URL="https://myapp-staging.fly.dev"
fi

if [ -z "$DEPLOY_URL" ]; then
    echo "❌ deploy-test gate FAIL: 不知道怎样部署（你没有配 vercel.json / deploy:staging / fly.toml）"
    exit 1
fi

# 2. 等 readiness
wait_for_health() {
    local url="$1/health"  # 假设你有 /health endpoint；改这里
    for i in {1..30}; do
        if curl -sf "$url" > /dev/null; then return 0; fi
        sleep 2
    done
    return 1
}

if ! wait_for_health "$DEPLOY_URL"; then
    echo "❌ deploy-test gate FAIL: 健康检查 30 次都没过"
    exit 1
fi

# 3. 主页能访问
if ! curl -sf "$DEPLOY_URL" > /dev/null; then
    echo "❌ deploy-test gate FAIL: 主页返回非 200"
    exit 1
fi

echo "✅ deploy-test gate PASS — $DEPLOY_URL"
[ "${1:-}" = "--capture" ] && echo "{\"failures\":[], \"url\":\"$DEPLOY_URL\"}"
exit 0
```

---

### 3.5 `gate-e2e.sh`（硬门禁）

```bash
#!/usr/bin/env bash
# scripts/gates/gate-e2e.sh — E2E 测试
#
# 默认 Playwright；按栈换 Cypress / Detox

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -d "tests/e2e" ] && [ -f "playwright.config.ts" ]; then
    npx playwright test --reporter=json --output-dir="$PWD/.gate-output/playwright" \
        > "$PWD/.gate-output/e2e-raw.json" 2>&1 \
        || echo "e2e exited non-zero"
elif [ -f "cypress.config.js" ]; then
    npx cypress run --reporter=json > "$PWD/.gate-output/e2e-raw.json" 2>&1 \
        || echo "e2e exited non-zero"
else
    echo "❌ e2e gate FAIL: 没找到 Playwright / Cypress 配置"
    exit 1
fi

# 解析结果
failures=$(node <<'NODE'
const fs = require('fs');
const raw = fs.readFileSync('.gate-output/e2e-raw.json', 'utf8');
const data = JSON.parse(raw);
const failed = [];
for (const suite of data.suites || []) {
    for (const spec of suite.specs || []) {
        if (spec.ok === false || spec.tests?.some(t => t.results?.[0]?.status !== 'expected')) {
            failed.push(spec.title);
        }
    }
}
console.log(JSON.stringify({ failures: failed.map(t => ({ test: t })) }));
NODE
)

# 基线对比
baseline_file="kb/gates/baseline.json"
if [ -f "$baseline_file" ]; then
    baseline_fails=$(jq -c '.gates.e2e.failures // []' "$baseline_file")
    delta=$(jq -c --argjson b "$baseline_fails" --argjson c "$failures" '$c - $b' <<< '{}' 2>/dev/null || echo '[]')
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
```

---

## 四、`.gates-state.json`（每跑一次更新一次）

`scripts/gates/gate-state-update.sh`：

```bash
#!/usr/bin/env bash
# 在每棒结束时跑，把当前 .gate-output/* 合并到 .gates-state.json

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

req_id="${REQ_ID:-unknown}"

cat > .gates-state.json <<EOF
{
  "REQ_ID": "$req_id",
  "updated_at": "$(date -u +%FT%T+00:00)",
  "baseline_source": "kb/gates/baseline.json",
  "gates": {
    "coverage": $(cat .gate-output/coverage.json 2>/dev/null || echo '{}'),
    "lint":     $(cat .gate-output/lint.json     2>/dev/null || echo '{}'),
    "deploy-test": $(cat .gate-output/deploy-test.json 2>/dev/null || echo '{}'),
    "e2e":      $(cat .gate-output/e2e.json      2>/dev/null || echo '{}')
  }
}
EOF
echo "✅ .gates-state.json 已更新"
```

> 这一份文件是要被 `.gitignore` 忽略的——它只作为当下的运行时证据。

---

## 五、整体跑法

```bash
# 一次性拍基线（每次新仓库只做一次，新需求也只补一次人工审核的更新）
./scripts/gates/gate-baseline.sh --snapshot

# 然后每棒结束：
./scripts/gates/gate-coverage.sh
./scripts/gates/gate-lint.sh
./scripts/gates/gate-deploy-test.sh
./scripts/gates/gate-e2e.sh

# 全部跑完，写状态
./scripts/gates/gate-state-update.sh

# 看状态
cat .gates-state.json | jq '.gates'
```

---

## 六、5 个脚本的最小可用版

你不用全懂。**先跑起来比懂重要**：

1. `cp assets/scripts/gate-baseline.sh /你的仓库/scripts/gates/`
2. `cp assets/scripts/gate-coverage.sh /你的仓库/scripts/gates/`
3. `cp assets/scripts/gate-lint.sh /你的仓库/scripts/gates/`
4. `cp assets/scripts/gate-deploy-test.sh /你的仓库/scripts/gates/`
5. `cp assets/scripts/gate-e2e.sh /你的仓库/scripts/gates/`
6. `mkdir -p scripts/gates/plugins && cp assets/scripts/plugins/* scripts/gates/plugins/`
7. `chmod +x scripts/gates/*.sh scripts/gates/plugins/*.sh`

然后改每个 script 里的栈特定 plugin（如果默认的不匹配你的栈）。

---

## 七、装 Git Hooks（自动每次提交前跑门禁）

`.git/hooks/pre-commit`：

```bash
#!/usr/bin/env bash
# 提交前自动过门禁（只跑 lint + coverage，快速反馈）
set -e
cd "$(git rev-parse --show-toplevel)"

echo "🛡️  pre-commit: 跑 lint + coverage..."
./scripts/gates/gate-lint.sh
./scripts/gates/gate-coverage.sh
```

`chmod +x .git/hooks/pre-commit`。

> 完整 E2E / 部署在合并到 main 之前跑（GitHub Actions 或 GitLab CI），不在每个 commit 跑（太慢）。

---

## 下一步

- 想看 3 个 MCP 怎么接 → [08-mcp.md](08-mcp.md)
- 想看「哪个门禁挂了怎么办」→ [09-runbook.md](09-runbook.md)
