"""aios_api.api.v1.auth —— 登录 / 当前用户 API（V1 新增）。"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import hash_password, user_to_jwt, verify_password
from ...db import get_session
from ...errors import AiosError, ErrorCode
from ...middleware.auth import JWT_COOKIE, CurrentUser
from ...models import Org, OrgMember, User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


# -----------------------------------------------------------------------------
# Pydantic
# -----------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=512)


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: datetime
    # V4: 多租户上下文 + RBAC 权限点
    org_id: str = ""
    role_key: str = ""
    perms: list[str] = Field(default_factory=list)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=512)


# -----------------------------------------------------------------------------
# 端点
# -----------------------------------------------------------------------------


@router.post("/login", summary="登录")
async def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserResponse:
    """V4 改造：登录时解析 org 上下文。

    - 若用户无任何 org：自动建一个「default-{username}」组织 + 该用户为 admin
    - 若用户有多个 org：选第一个作为当前 org
    - role_key 默认按 user.role 决定（V0 admin -> admin / V0 viewer -> viewer）
    """
    result = await session.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AiosError(
            ErrorCode.E_AUTH_INVALID_CRED,
            "用户名或密码错误",
            http_status=401,
        )

    # V4: 解析当前 org + role
    org_id, role_key = await _resolve_default_org(session, user)
    token = user_to_jwt(user, org_id=org_id, role_key=role_key)

    # httpOnly cookie
    response.set_cookie(
        key=JWT_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role.value,
        created_at=user.created_at,
        org_id=org_id,
        role_key=role_key,
    )


async def _resolve_default_org(session: AsyncSession, user: User) -> tuple[str, str]:
    """V4: 给当前用户挑默认 org（用于登录后 token 的 org_id/role_key 上下文）。

    规则：
      1. 查 org_members 找用户已有 org；按 joined_at asc 取最早一个
      2. 没有任何 org：自动建一个「{username}-default」+ 用户为 admin
      3. role_key 转换：V0 admin -> admin，V0 viewer -> viewer（其余默认 viewer）
    """
    result = await session.execute(
        select(OrgMember)
        .where(OrgMember.user_id == user.id)
        .order_by(OrgMember.joined_at.asc())
        .limit(1)
    )
    member = result.scalar_one_or_none()
    if member is not None:
        return member.org_id, member.role_key

    # 自动建一个 default org + 该用户为 admin
    new_org = Org(
        id=str(uuid4()),
        name=f"{user.username} 的默认组织",
        slug=f"{user.username}-default"[:64],
    )
    session.add(new_org)
    role_key = "admin" if user.role == UserRole.admin else "viewer"
    session.add(
        OrgMember(
            org_id=new_org.id,
            user_id=user.id,
            role_key=role_key,
        )
    )
    await session.commit()
    return new_org.id, role_key


@router.post("/logout", summary="登出")
async def logout(response: Response) -> dict:
    response.delete_cookie(JWT_COOKIE)
    return {"ok": True}


@router.get("/me", response_model=UserResponse, summary="当前用户")
async def me(user: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]) -> UserResponse:
    """V4: 返回多租户上下文（org_id / role_key）和当前用户在所在组织的 perms 列表。"""
    result = await session.execute(select(User).where(User.id == user["sub"]))
    u = result.scalar_one_or_none()
    if u is None:
        raise AiosError(ErrorCode.E_AUTH_REQUIRED, "用户不存在", http_status=401)
    return UserResponse(
        id=u.id,
        username=u.username,
        role=u.role.value,
        created_at=u.created_at,
        org_id=user.get("org_id", ""),
        role_key=user.get("role_key", ""),
        perms=list(user.get("perms", [])),
    )


@router.post("/change-password", summary="改密码")
async def change_password(
    body: ChangePasswordRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    result = await session.execute(select(User).where(User.id == user["sub"]))
    u = result.scalar_one_or_none()
    if u is None or not verify_password(body.old_password, u.password_hash):
        raise AiosError(ErrorCode.E_AUTH_INVALID_CRED, "旧密码错误", http_status=401)
    u.password_hash = hash_password(body.new_password)
    await session.commit()
    return {"ok": True}
