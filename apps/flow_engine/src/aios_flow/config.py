"""aios_flow.config —— flow_engine 配置。"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """flow_engine 配置。"""

    model_config = SettingsConfigDict(env_prefix="AIOS_FLOW_", env_file=".env", extra="ignore")

    app_version: str = "0.2.0"
    env: str = "dev"
    log_level: str = "INFO"

    # Temporal
    temporal_host: str = "temporal:7233"
    temporal_namespace: str = "default"
    task_queue: str = "aios-flow-engine"

    # 与后端 API 通信
    api_url: str = "http://api:8080"

    # 调度器
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 60


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
