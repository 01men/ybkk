#!/usr/bin/env bash
# 元冰可可 AIOS — 升级 / 回滚脚本
# 用法:
#   ./upgrade.sh 0.2.0           # 升级到 0.2.0
#   ./upgrade.sh --rollback      # 回滚到上一版本
#   ./upgrade.sh --list          # 查看可用版本

set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${DEPLOY_DIR}"

# 当前版本
current_version() {
  grep "^AIOS_VERSION=" .env | cut -d= -f2
}

# 上一个版本（从备份里取最近的 .env）
last_version() {
  local last_backup
  last_backup=$(ls -td backups/*/env.backup 2>/dev/null | head -1 || true)
  if [[ -n "${last_backup}" ]]; then
    grep "^AIOS_VERSION=" "${last_backup}" | cut -d= -f2
  else
    echo ""
  fi
}

case "${1:-}" in
  --list)
    echo "可用版本（本地镜像）："
    docker images --format "  {{.Tag}}" ghcr.io/01men/ybkk-api | sort -V | uniq
    ;;
  --rollback)
    target=$(last_version)
    if [[ -z "${target}" ]]; then
      echo "❌ 没有可回滚的历史版本"
      exit 1
    fi
    echo "回滚到 ${target}"
    sed -i.bak "s/^AIOS_VERSION=.*/AIOS_VERSION=${target}/" .env
    docker-compose pull
    docker-compose up -d
    echo "✅ 回滚完成"
    ;;
  "")
    echo "用法: $0 <version> | --rollback | --list"
    exit 1
    ;;
  *)
    target="$1"
    echo "升级到 ${target}"
    sed -i.bak "s/^AIOS_VERSION=.*/AIOS_VERSION=${target}/" .env
    docker-compose pull
    docker-compose up -d
    echo "✅ 升级完成"
    ;;
esac