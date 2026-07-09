#!/usr/bin/env bash
# scripts/gates/gate-baseline.sh — 基线管理：拍快照 / 比对 / 查状态
#
# 用法：
#   ./scripts/gates/gate-baseline.sh --snapshot    # 跑一遍所有门禁，写成基线
#   ./scripts/gates/gate-baseline.sh status         # 看基线状态
#   ./scripts/gates/gate-baseline.sh diff <gate>    # 看某门禁在 baseline 之后的差集
#
# 依赖：bash, jq

set -euo pipefail

# 关键修正：脚本位于 <repo>/coding_group/assets/scripts/，往上三级才是仓库根
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
BASELINE_FILE="$PROJECT_ROOT/coding_group/kb/gates/baseline.json"
GATE_OUTPUT_DIR="$PROJECT_ROOT/.gate-output"

mkdir -p "$GATE_OUTPUT_DIR"
mkdir -p "$(dirname "$BASELINE_FILE")"

# 检查依赖
for cmd in jq git; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ 缺少依赖: $cmd"
        echo "   安装：brew install jq  (mac)  /  apt install jq  (ubuntu)"
        exit 1
    fi
done

# 跑一次全部 5 道门禁，输出到 $GATE_OUTPUT_DIR
run_all_gates() {
    bash "$SCRIPT_DIR/gate-coverage.sh"    --capture > "$GATE_OUTPUT_DIR/coverage.json"    2>/dev/null || true
    bash "$SCRIPT_DIR/gate-lint.sh"        --capture > "$GATE_OUTPUT_DIR/lint.json"        2>/dev/null || true
    bash "$SCRIPT_DIR/gate-deploy-test.sh" --capture > "$GATE_OUTPUT_DIR/deploy-test.json" 2>/dev/null || true
    bash "$SCRIPT_DIR/gate-e2e.sh"         --capture > "$GATE_OUTPUT_DIR/e2e.json"         2>/dev/null || true
}

snapshot() {
    echo "🔍 跑全部门禁，生成基线快照…"
    run_all_gates

    cat > "$BASELINE_FILE" <<EOF
{
  "captured_at": "$(date -u +%FT%T+00:00)",
  "commit_sha": "$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "gates": {
    "coverage":     $(cat "$GATE_OUTPUT_DIR/coverage.json"),
    "lint":         $(cat "$GATE_OUTPUT_DIR/lint.json"),
    "deploy-test":  $(cat "$GATE_OUTPUT_DIR/deploy-test.json"),
    "e2e":          $(cat "$GATE_OUTPUT_DIR/e2e.json")
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