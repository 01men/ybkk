"""aios_api.auth —— JWT 签发 + 校验（参见 02-design-doc.md V1 §3 + TASK-V1-002）。"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from typing import Any

from ..config import get_settings
from ..errors import AiosError, ErrorCode
from ..models import User, UserRole


def _sign(payload_bytes: bytes) -> bytes:
    """HS256 签名（不依赖 PyJWT，标准库实现）。"""
    secret = get_settings().jwt_secret.get_secret_value().encode("utf-8")
    return hmac.new(secret, payload_bytes, hashlib.sha256).digest()


def encode_jwt(payload: dict[str, Any], ttl_seconds: int = 86400 * 7) -> str:
    """签发 JWT（HS256 + 标准 claim）。"""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    body = {**payload, "iat": now, "exp": now + ttl_seconds}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    body_b64 = _b64url(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{body_b64}".encode("ascii")
    sig = _sign(signing_input)
    return f"{header_b64}.{body_b64}.{_b64url(sig)}"


def decode_jwt(token: str) -> dict[str, Any]:
    """校验 + 解析 JWT。失败抛 E_AUTH_TOKEN_INVALID。"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("malformed")
        header_b64, body_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{body_b64}".encode("ascii")
        expected_sig = _sign(signing_input)
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("signature mismatch")
        body = json.loads(_b64url_decode(body_b64).decode("utf-8"))
        if body.get("exp", 0) < int(time.time()):
            raise ValueError("expired")
        return body
    except Exception as e:
        raise AiosError(
            ErrorCode.E_AUTH_TOKEN_INVALID,
            "JWT 解析失败",
            http_status=401,
            context={"type": type(e).__name__},
        ) from e


def _b64url(data: bytes) -> str:
    return (
        __import__("base64").urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    )


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return __import__("base64").urlsafe_b64decode(s + "=" * padding)


# -----------------------------------------------------------------------------
# 密码哈希（PBKDF2-HMAC-SHA256，标准库实现；不依赖 passlib）
# -----------------------------------------------------------------------------


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000${__import__('base64').urlsafe_b64encode(salt).decode()}${__import__('base64').urlsafe_b64encode(dk).decode()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        algo, iters, salt_b64, dk_b64 = hashed.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = __import__("base64").urlsafe_b64decode(salt_b64)
        expected = __import__("base64").urlsafe_b64decode(dk_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iters)
        )
        return hmac.compare_digest(expected, actual)
    except Exception:
        return False


def user_to_jwt(user: User) -> str:
    return encode_jwt(
        {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
        }
    )


__all__ = [
    "encode_jwt",
    "decode_jwt",
    "hash_password",
    "verify_password",
    "user_to_jwt",
]
