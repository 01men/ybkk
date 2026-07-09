"""aios_api.config —— 配置管理（基于 pydantic-settings）。

所有配置从 .env 读取；私有化部署 install.sh 会自动生成。
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """平台运行时配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 基础
    app_name: str = "aios-api"
    app_version: str = "0.1.0"
    env: Literal["dev", "staging", "production"] = "dev"
    log_level: str = "INFO"
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "aios"
    postgres_user: str = "aios"
    postgres_password: SecretStr = SecretStr("changeme")

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr = SecretStr("changeme")

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "aios"
    minio_secret_key: SecretStr = SecretStr("changeme")
    minio_bucket: str = "aios-uploads"
    minio_secure: bool = False

    # JWT
    jwt_secret: SecretStr = SecretStr("changeme-changeme-changeme-changeme")
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 60
    jwt_refresh_ttl_days: int = 7

    # KMS（本地轻量密钥；生产建议外接 Vault）
    kms_key: SecretStr = SecretStr("0" * 64)

    # LLM 网关
    llm_provider: Literal["qwen-local", "openai", "anthropic"] = "qwen-local"
    llm_qwen_base_url: str = "http://localhost:8001"
    llm_openai_api_key: SecretStr | None = None
    llm_anthropic_api_key: SecretStr | None = None

    # 限额
    datasource_limit_per_tenant: int = 50
    file_upload_limit_mb: int = 200
    llm_rate_limit_per_min: int = 60

    # 置信度阈值
    ontology_confidence_threshold: float = 0.6

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_sync_url(self) -> str:
        """Alembic 用同步驱动。"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """全局单例配置。"""
    return Settings()