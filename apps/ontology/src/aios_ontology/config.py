"""aios_ontology.config —— 本体服务配置。"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AIOS_ONT_", env_file=".env", extra="ignore")

    app_version: str = "0.2.0"
    log_level: str = "INFO"

    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "CHANGEME"
    neo4j_database: str = "neo4j"

    api_url: str = "http://api:8000"
    api_token: str = ""


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
