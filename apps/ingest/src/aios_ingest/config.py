"""aios_ingest.config —— 摄取服务配置。"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIOS_INGEST_", env_file=".env", extra="ignore")

    app_version: str = "0.2.0"
    log_level: str = "INFO"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "aios"
    minio_secret_key: str = "CHANGEME"
    minio_bucket: str = "aios-ingest"
    minio_secure: bool = False

    # 后端 API
    api_url: str = "http://api:8000"
    api_token: str = ""  # 内部服务 token（V2 用预共享 secret）

    # Redis 队列
    redis_url: str = "redis://redis:6379/0"

    # ASR
    asr_provider: str = "local"  # local | aliyun
    asr_local_model: str = "base"  # whisper 模型大小
    aliyun_access_key_id: str = ""
    aliyun_access_key_secret: str = ""


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
