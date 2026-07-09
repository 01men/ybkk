#!/usr/bin/env bash
# =============================================================================
# 元冰可可 AIOS — 一键私有化部署脚本
# =============================================================================
# 用法:
#   ./install.sh                  # 默认安装（推荐配置）
#   ./install.sh --minimal        # 最小安装（仅核心组件）
#   ./install.sh --with-monitoring # 含 Prometheus / Grafana / Loki
#   ./install.sh --check          # 仅检查环境
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# 颜色与日志
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -----------------------------------------------------------------------------
# 默认值
# -----------------------------------------------------------------------------
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${DEPLOY_DIR}/../.." && pwd)"
COMPOSE_FILE="${DEPLOY_DIR}/docker-compose.yml"
ENV_FILE="${DEPLOY_DIR}/.env"
WITH_MONITORING=false
MINIMAL=false
CHECK_ONLY=false

# -----------------------------------------------------------------------------
# 参数解析
# -----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-monitoring) WITH_MONITORING=true; shift ;;
    --minimal)        MINIMAL=true; shift ;;
    --check)          CHECK_ONLY=true; shift ;;
    -h|--help)
      echo "Usage: $0 [--with-monitoring] [--minimal] [--check]"
      exit 0
      ;;
    *) log_err "未知参数: $1"; exit 1 ;;
  esac
done

# -----------------------------------------------------------------------------
# 硬件预检
# -----------------------------------------------------------------------------
check_hardware() {
  log_info "硬件预检..."

  local cpu_mem
  cpu_mem=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 0)

  local cpu_cores
  cpu_cores=$(nproc 2>/dev/null || echo 0)

  if [[ ${CHECK_ONLY} == true ]]; then
    log_info "CPU 核心: ${cpu_cores}"
    log_info "内存 (GB): ${cpu_mem}"
    return 0
  fi

  if [[ ${cpu_cores} -lt 4 ]]; then
    log_err "CPU 核心数不足（${cpu_cores} < 4）。最小要求 4C，推荐 8C+"
    exit 1
  fi

  if [[ ${cpu_mem} -lt 8 ]]; then
    log_err "内存不足（${cpu_mem}GB < 8GB）。最小要求 8GB，推荐 16GB+"
    exit 1
  fi

  log_ok "硬件预检通过: ${cpu_cores}C ${cpu_mem}GB"
}

# -----------------------------------------------------------------------------
# 软件预检
# -----------------------------------------------------------------------------
check_software() {
  log_info "软件预检..."

  for cmd in docker docker-compose curl; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      log_err "缺少依赖: ${cmd}"
      exit 1
    fi
  done

  if ! docker info >/dev/null 2>&1; then
    log_err "Docker daemon 未运行。请先启动 Docker。"
    exit 1
  fi

  log_ok "软件预检通过"
}

# -----------------------------------------------------------------------------
# 生成 .env
# -----------------------------------------------------------------------------
generate_env() {
  if [[ -f "${ENV_FILE}" ]]; then
    log_warn ".env 已存在，跳过生成（使用现有配置）"
    return 0
  fi

  log_info "生成 .env..."

  local pg_password
  pg_password=$(openssl rand -hex 16 2>/dev/null || head -c 32 /dev/urandom | xxd -p -c 32)
  local neo4j_password
  neo4j_password=$(openssl rand -hex 16 2>/dev/null || head -c 32 /dev/urandom | xxd -p -c 32)
  local jwt_secret
  jwt_secret=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p -c 64)
  local kms_key
  kms_key=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p -c 64)

  cat > "${ENV_FILE}" <<EOF
# 元冰可可 AIOS — 私有化部署配置
# ⚠️ 请勿将本文件 commit 进 git

# 部署时间
AIOS_VERSION=0.1.0
AIOS_DEPLOYED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# PostgreSQL
POSTGRES_DB=aios
POSTGRES_USER=aios
POSTGRES_PASSWORD=${pg_password}

# Neo4j
NEO4J_AUTH=neo4j/${neo4j_password}

# Redis（无密码；私有化内部网络）
REDIS_PASSWORD=

# MinIO
MINIO_ROOT_USER=aios
MINIO_ROOT_PASSWORD=${pg_password}

# JWT
JWT_SECRET=${jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MIN=60
JWT_REFRESH_TTL_DAYS=7

# KMS（本地轻量 KMS）
AIOS_KMS_KEY=${kms_key}

# 控制台
AIOS_CONSOLE_PORT=8443
AIOS_API_PORT=8000

# LLM 网关（默认走本地 Qwen2.5-72B；可切换）
LLM_PROVIDER=qwen-local
LLM_QWEN_BASE_URL=http://qwen:8000
LLM_OPENAI_BASE_URL=
LLM_OPENAI_API_KEY=
LLM_ANTHROPIC_BASE_URL=
LLM_ANTHROPIC_API_KEY=

# 监控（仅 --with-monitoring 时使用）
GRAFANA_ADMIN_PASSWORD=${pg_password}

# 日志级别
LOG_LEVEL=INFO
EOF

  chmod 600 "${ENV_FILE}"
  log_ok ".env 已生成（密码已随机化）"
}

# -----------------------------------------------------------------------------
# 拉镜像 / 起容器
# -----------------------------------------------------------------------------
start_containers() {
  log_info "拉取镜像..."
  cd "${DEPLOY_DIR}"

  local profiles=()
  if [[ ${WITH_MONITORING} == true ]]; then
    profiles+=(--profile monitoring)
  fi

  docker-compose "${profiles[@]}" pull

  log_info "启动容器..."
  docker-compose "${profiles[@]}" up -d

  log_ok "容器已启动"
}

# -----------------------------------------------------------------------------
# 健康检查
# -----------------------------------------------------------------------------
wait_healthy() {
  log_info "等待服务健康..."

  local services=("postgres" "neo4j" "redis" "minio" "api" "web")
  local max_attempts=60
  local attempt=0

  while [[ ${attempt} -lt ${max_attempts} ]]; do
    local all_healthy=true

    for svc in "${services[@]}"; do
      local status
      status=$(docker inspect --format='{{.State.Health.Status}}' "aios_${svc}_1" 2>/dev/null || echo "unknown")
      if [[ "${status}" != "healthy" ]]; then
        all_healthy=false
        break
      fi
    done

    if [[ ${all_healthy} == true ]]; then
      log_ok "所有核心服务已就绪"
      return 0
    fi

    attempt=$((attempt + 1))
    sleep 5
    log_info "等待中... (${attempt}/${max_attempts})"
  done

  log_err "服务启动超时。运行 'docker-compose logs' 查看详情。"
  return 1
}

# -----------------------------------------------------------------------------
# 输出访问信息
# -----------------------------------------------------------------------------
print_access_info() {
  local host_ip
  host_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

  echo ""
  echo -e "${GREEN}================================================================${NC}"
  echo -e "${GREEN}  元冰可可 AIOS 部署完成${NC}"
  echo -e "${GREEN}================================================================${NC}"
  echo ""
  echo -e "  控制台: ${BLUE}https://${host_ip}:${AIOS_CONSOLE_PORT:-8443}${NC}"
  echo -e "  API:    ${BLUE}http://${host_ip}:${AIOS_API_PORT:-8000}${NC}"
  echo -e "  默认账号: ${YELLOW}admin / changeme${NC} (首次登录后请立即修改)"
  echo ""
  echo -e "  备份命令: ${BLUE}bash ${DEPLOY_DIR}/backup.sh${NC}"
  echo -e "  升级命令: ${BLUE}bash ${DEPLOY_DIR}/upgrade.sh <version>${NC}"
  echo -e "  回滚命令: ${BLUE}bash ${DEPLOY_DIR}/upgrade.sh --rollback${NC}"
  echo ""
  echo -e "  文档: ${BLUE}${PROJECT_ROOT}/README.md${NC}"
  echo -e "${GREEN}================================================================${NC}"
}

# -----------------------------------------------------------------------------
# 主流程
# -----------------------------------------------------------------------------
main() {
  echo ""
  echo -e "${BLUE}元冰可可 AIOS 一键私有化部署${NC}"
  echo ""

  check_hardware
  check_software

  if [[ ${CHECK_ONLY} == true ]]; then
    log_ok "环境检查完成。"
    exit 0
  fi

  generate_env
  start_containers
  wait_healthy
  print_access_info
}

main "$@"