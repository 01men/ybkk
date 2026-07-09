"""aios_api.middleware.auth —— 鉴权中间件（V1 新增）。"""
from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Request

from ..auth import decode_jwt
from ..errors import AiosError, ErrorCode
from ..models import UserRole


JWT_COOKIE = "aios_token"


async def get_current_user(
    request: Request,
    token: Annotated[str | None, Cookie(alias=JWT_COOKIE)] = None,
) -> dict:
    """从 cookie 读 JWT，校验后返回 payload（sub/username/role）。"""
    if not token:
        raise AiosError(
            ErrorCode.E_AUTH_REQUIRED,
            "未登录或 token 缺失",
            http_status=401,
        )
    payload = decode_jwt(token)
    # 把 user info 挂到 request.state，方便 audit
    request.state.actor = payload.get("username", "unknown")
    request.state.user_role = UserRole(payload.get("role", "viewer"))
    return payload


CurrentUser = Annotated[dict, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> dict:
    """要求 admin 角色（V1 简化为单角色）。"""
    if user.get("role") != "admin":
        raise AiosError(
            ErrorCode.E_AUTH_FORBIDDEN,
            "需要 admin 角色",
            http_status=403,
            context={"actual_role": user.get("role")},
        )
    return user


AdminUser = Annotated[dict, Depends(require_admin)]
