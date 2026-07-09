"""tests.config —— 配置管理单元测试。"""
from __future__ import annotations

import os

import pytest
from pydantic import SecretStr

from aios_api.config import Settings, get_settings


class TestSettings:
    def test_default_values(self) -> None:
        s = Settings()
        assert s.app_name == "aios-api"
        assert s.app_version == "0.1.0"
        assert s.env == "dev"
        assert s.api_port == 8000

    def test_postgres_url_format(self) -> None:
        s = Settings(
            postgres_host="db.local",
            postgres_port=5432,
            postgres_db="aios",
            postgres_user="aios",
            postgres_password=SecretStr("secret"),
        )
        assert s.postgres_url == "postgresql+asyncpg://aios:secret@db.local:5432/aios"
        assert s.postgres_sync_url == "postgresql+psycopg2://aios:secret@db.local:5432/aios"

    def test_secrets_are_secret_str(self) -> None:
        s = Settings()
        assert isinstance(s.postgres_password, SecretStr)
        assert isinstance(s.jwt_secret, SecretStr)
        assert isinstance(s.kms_key, SecretStr)
        # 验证打印不会泄露明文
        assert "changeme" not in repr(s.jwt_secret)

    def test_get_settings_is_singleton(self) -> None:
        a = get_settings()
        b = get_settings()
        assert a is b

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AIOS_API_PORT", "9999")
        monkeypatch.setenv("AIOS_LOG_LEVEL", "DEBUG")
        get_settings.cache_clear()
        s = get_settings()
        assert s.api_port == 9999
        assert s.log_level == "DEBUG"