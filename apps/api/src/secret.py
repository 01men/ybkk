"""aios_api.secret —— 数据源凭证加密 / 解密（参见 TASK-061）。

本地轻量 KMS：Fernet 对称加密（AES-128-CBC + HMAC）。
生产环境建议外接 HashiCorp Vault，替换 SecretService 即可。
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings
from ..errors import AiosError, ErrorCode


def _derive_key() -> bytes:
    """从 .env 的 AIOS_KMS_KEY 派生出 32 字节 URL-safe base64 key。"""
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
    """数据源凭证的加密存储与解密使用。

    用法：
        svc = SecretService()
        encrypted = svc.encrypt('{"password": "secret"}')
        plain = svc.decrypt(encrypted)
    """

    def encrypt(self, plaintext: str) -> str:
        """加密 → 返回 URL-safe base64 字符串（落库到 connection_json_encrypted）。"""
        return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """解密 → 返回明文。

        任何解密失败抛 E_SYS_INTERNAL（密钥错误或数据被篡改）。
        """
        try:
            return _get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as e:
            raise AiosError(
                ErrorCode.E_SYS_INTERNAL,
                "数据源凭证解密失败（密钥不匹配或数据被篡改）",
                http_status=500,
                context={"type": type(e).__name__},
            ) from e


# 单例（agent-develop prompt 不鼓励全局可变状态，但 SecretService 内部只读，是安全的）
_default = SecretService()


def get_secret_service() -> SecretService:
    return _default