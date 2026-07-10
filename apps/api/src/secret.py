"""SecretService - Fernet-based encryption for datasource credentials.

Lightweight KMS (AES-128-CBC + HMAC).
In production, replace SecretService with HashiCorp Vault integration.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings
from .errors import AiosError, ErrorCode


def _derive_key() -> bytes:
    """Derive a 32-byte URL-safe base64 key from AIOS_KMS_KEY in .env."""
    raw = get_settings().kms_key.get_secret_value().encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest)


_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_derive_key())
    return _fernet


class SecretService:
    """Encrypt / decrypt datasource credentials."""

    def encrypt(self, plaintext: str) -> str:
        """Encrypt -> URL-safe base64 string (stored in connection_json_encrypted)."""
        return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt -> plaintext.

        Raises E_SYS_INTERNAL on failure (wrong key or tampered data).
        """
        try:
            return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as e:
            raise AiosError(
                ErrorCode.E_SYS_INTERNAL,
                "decryption failed: invalid key or tampered ciphertext",
            ) from e


_secret_service: SecretService | None = None


def get_secret_service() -> SecretService:
    """Return the singleton SecretService."""
    global _secret_service
    if _secret_service is None:
        _secret_service = SecretService()
    return _secret_service


def encrypt_datasource_credentials(plaintext: str) -> str:
    """Convenience wrapper used by datasource CRUD."""
    return get_secret_service().encrypt(plaintext)


def decrypt_datasource_credentials(ciphertext: str) -> str:
    """Convenience wrapper used by datasource read paths."""
    return get_secret_service().decrypt(ciphertext)