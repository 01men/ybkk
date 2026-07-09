"""tests.secret —— KMS 加密解密测试。"""
from __future__ import annotations

import pytest
from pydantic import SecretStr

from aios_api.config import Settings
from aios_api.errors import AiosError, ErrorCode
from aios_api.secret import SecretService, get_secret_service


@pytest.fixture(autouse=True)
def _kms_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """每个测试都用稳定密钥，方便复现。"""
    # 64 hex chars
    monkeypatch.setenv("AIOS_KMS_KEY", "0" * 64)


class TestSecretService:
    def test_roundtrip(self) -> None:
        svc = SecretService()
        plain = '{"password": "my-secret-password"}'
        encrypted = svc.encrypt(plain)
        assert encrypted != plain
        assert svc.decrypt(encrypted) == plain

    def test_encrypt_produces_different_ciphertexts(self) -> None:
        """Fernet 默认每次随机 nonce → 同样明文不同密文。"""
        svc = SecretService()
        plain = "same input"
        c1 = svc.encrypt(plain)
        c2 = svc.encrypt(plain)
        assert c1 != c2
        assert svc.decrypt(c1) == plain
        assert svc.decrypt(c2) == plain

    def test_decrypt_with_wrong_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = SecretService()
        encrypted = svc.encrypt("payload")

        # 切换密钥
        monkeypatch.setenv("AIOS_KMS_KEY", "f" * 64)
        # 触发重算
        import aios_api.secret as sm

        sm._fernet = None

        with pytest.raises(AiosError) as exc_info:
            svc.decrypt(encrypted)
        assert exc_info.value.code == ErrorCode.E_SYS_INTERNAL

    def test_default_singleton(self) -> None:
        s1 = get_secret_service()
        s2 = get_secret_service()
        assert s1 is s2

    def test_does_not_leak_plaintext_in_repr(self) -> None:
        svc = SecretService()
        encrypted = svc.encrypt("top-secret")
        # repr/打印不应包含明文
        assert "top-secret" not in encrypted
        assert "top-secret" not in repr(encrypted)