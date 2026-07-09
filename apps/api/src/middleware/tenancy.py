"""aios_api.middleware.tenancy —— V3 多租户上下文。"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request

from ..auth import decode_jwt
from ..errors import AiosError, ErrorCode
from ..models import OrgMember


@dataclass
class OrgContext:
    """当前请求的 org + 用户在该组织的角色。"""

    user_id: str
    username: str
    org_id: str
    role_key: str  # admin | engineer | operator | viewer

    def __repr__(self) -> str:
        return f"<OrgContext user={self.username} org={self.org_id} role={self.role_key}>"


def get_org_context(request: Request) -> OrgContext:
    """从 Authorization header 解析 JWT，得到 OrgContext。

    V3 多租户强约束：每个业务 API 都必须经过本依赖。
    """
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise AiosError(
            ErrorCode.E_AUTH_TOKEN_INVALID,
            "缺少 Authorization Bearer token",
            http_status=401,
        )
    token = auth.split(" ", 1)[1].strip()
    payload = decode_jwt(token)
    org_id = payload.get("org_id", "")
    role_key = payload.get("role_key", "")
    if not org_id:
        raise AiosError(
            ErrorCode.E_AUTH_TOKEN_INVALID,
            "token 缺少 org_id claim（V3 多租户必需）",
            http_status=401,
        )
    if role_key not in {"admin", "engineer", "operator", "viewer"}:
        raise AiosError(
            ErrorCode.E_AUTH_TOKEN_INVALID,
            f"非法 role_key: {role_key}",
            http_status=401,
        )
    return OrgContext(
        user_id=payload.get("sub", ""),
        username=payload.get("username", ""),
        org_id=org_id,
        role_key=role_key,
    )


def require_org_member(org: OrgContext = Depends(get_org_context)) -> OrgContext:
    """依赖入口：业务 API 加这个 dep 即可拿到 org 上下文。"""
    return org


__all__ = ["OrgContext", "get_org_context", "require_org_member"]
