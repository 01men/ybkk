"""V4 JWT 单元测试 —— JWT_CURRENT_VERSION 强制重新签发 + perms claim。"""
from __future__ import annotations

import time

import pytest

from aios_api.auth import (
    JWT_CURRENT_VERSION,
    decode_jwt,
    encode_jwt,
    hash_password,
    user_to_jwt,
    verify_password,
)
from aios_api.errors import AiosError
from aios_api.middleware.rbac import (
    ALL_PERMISSIONS,
    ROLE_PERMISSIONS,
    has_permission,
    permissions_for,
)


# ---- JWT ver 强制重新签发 --------------------------------------------------


def test_jwt_current_version_is_4():
    assert JWT_CURRENT_VERSION == 4


def test_encode_jwt_includes_ver():
    token = encode_jwt({"sub": "u1", "username": "x"})
    body = decode_jwt(token)
    assert body.get("ver") == JWT_CURRENT_VERSION


def test_old_ver_token_rejected():
    """V4: ver<4 的旧 token 一律拒绝。"""
    # 模拟旧 token（V3 时期没 ver 字段）
    old_token = encode_jwt(
        {"sub": "u1", "username": "x", "ver": 3}  # ver=3 是 V3
    )
    with pytest.raises(AiosError):
        decode_jwt(old_token)


def test_no_ver_token_rejected():
    """V4: 完全没有 ver 字段的 token 也拒绝。"""
    no_ver_token = encode_jwt({"sub": "u1", "username": "x"}, ttl_seconds=86400 * 7)
    # encode_jwt 会自动加 ver=4，所以这里无法直接构造；改用 raw jwt
    import base64
    import hmac
    import json
    from aios_api.config import get_settings
    header = {"alg": "HS256", "typ": "JWT"}
    body = {"sub": "u1", "username": "x", "iat": int(time.time()), "exp": int(time.time()) + 86400}
    h = base64.urlsafe_b64encode(json.dumps(header, separators=(",", ":")).encode()).rstrip(b"=").decode()
    b = base64.urlsafe_b64encode(json.dumps(body, separators=(",", ":")).encode()).rstrip(b"=").decode()
    signing_input = f"{h}.{b}".encode()
    secret = get_settings().jwt_secret.get_secret_value().encode()
    sig = base64.urlsafe_b64encode(hmac.new(secret, signing_input, __import__('hashlib').sha256).digest()).rstrip(b"=").decode()
    raw = f"{h}.{b}.{sig}"
    with pytest.raises(AiosError):
        decode_jwt(raw)


# ---- perms claim -----------------------------------------------------------


def test_user_to_jwt_includes_perms():
    """V4: user_to_jwt 自动按 role_key 解析 ROLE_PERMISSIONS 写入 perms 列表。"""
    from aios_api.models import User, UserRole
    u = User(id="u1", username="alice", password_hash="x", role=UserRole.ADMIN)
    token = user_to_jwt(u, org_id="org-1", role_key="admin")
    body = decode_jwt(token)
    assert body.get("org_id") == "org-1"
    assert body.get("role_key") == "admin"
    assert set(body.get("perms", [])) == set(ALL_PERMISSIONS)


def test_user_to_jwt_viewer_has_only_6_perms():
    from aios_api.models import User, UserRole
    u = User(id="u2", username="bob", password_hash="x", role=UserRole.VIEWER)
    token = user_to_jwt(u, org_id="org-2", role_key="viewer")
    body = decode_jwt(token)
    assert set(body.get("perms", [])) == set(ROLE_PERMISSIONS["viewer"])
    assert len(body.get("perms", [])) == 6


def test_user_to_jwt_unknown_role_empty_perms():
    from aios_api.models import User, UserRole
    u = User(id="u3", username="c", password_hash="x", role=UserRole.ADMIN)
    token = user_to_jwt(u, org_id="o", role_key="nonexistent")
    body = decode_jwt(token)
    assert body.get("perms") == []


# ---- 密码 hash ------------------------------------------------------------


def test_hash_password_roundtrip():
    h = hash_password("hello123")
    assert verify_password("hello123", h) is True
    assert verify_password("wrong", h) is False


# ---- 关键权限判定（V3 沿用） ---------------------------------------------


def test_admin_has_all_perms():
    assert ROLE_PERMISSIONS["admin"] == frozenset(ALL_PERMISSIONS)


def test_role_level_monotonic():
    from aios_api.middleware.rbac import ROLE_LEVEL
    assert ROLE_LEVEL["admin"] > ROLE_LEVEL["engineer"] > ROLE_LEVEL["operator"] > ROLE_LEVEL["viewer"]


def test_viewer_no_write():
    assert has_permission("viewer", "datasource.read") is True
    assert has_permission("viewer", "datasource.write") is False


def test_engineer_can_write_but_not_org_admin():
    assert has_permission("engineer", "datasource.write") is True
    assert has_permission("engineer", "org.delete") is False


def test_permissions_for_unknown_role_empty():
    assert permissions_for("ghost") == frozenset()