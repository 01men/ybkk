#!/usr/bin/env bash
# 元冰可可 AIOS — 备份脚本
# 每 6 小时跑一次（cron: 0 */6 * * * /opt/aios/deploy/compose/backup.sh）
# 保留 7 天本地 + 30 天远程（可选 MinIO 备份 bucket）

set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${DEPLOY_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS=7

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] 开始备份到 ${BACKUP_DIR}"

# 备份 PostgreSQL
docker exec aios_postgres_1 pg_dump -U aios aios | gzip > "${BACKUP_DIR}/postgres.sql.gz"

# 备份 Neo4j（cypher-shell 导出）
docker exec aios_neo4j_1 neo4j-admin dump --database=neo4j --to=/tmp/neo4j.dump
docker cp aios_neo4j_1:/tmp/neo4j.dump "${BACKUP_DIR}/neo4j.dump"

# 备份 MinIO（mc mirror）
docker run --rm -v aios_minio-data:/data -v "${BACKUP_DIR}:/backup" alpine \
  tar czf /backup/minio-data.tar.gz -C /data .

# 备份 .env
cp "${DEPLOY_DIR}/.env" "${BACKUP_DIR}/env.backup"

echo "[$(date)] 备份完成"

# 清理 7 天前的备份
find "${DEPLOY_DIR}/backups" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} +
echo "[$(date)] 清理 ${RETENTION_DAYS} 天前的旧备份"