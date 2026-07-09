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
from ...models import User, UserRole

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
    result = await session.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise AiosError(
            ErrorCode.E_AUTH_INVALID_CRED,
            "用户名或密码错误",
            http_status=401,
        )
    token = user_to_jwt(user)
    # httpOnly cookie
    response.set_cookie(
        key=JWT_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return UserResponse(
        id=user.id, username=user.username, role=user.role.value, created_at=user.created_at
    )


@router.post("/logout", summary="登出")
async def logout(response: Response) -> dict:
    response.delete_cookie(JWT_COOKIE)
    return {"ok": True}


@router.get("/me", response_model=UserResponse, summary="当前用户")
async def me(user: CurrentUser, session: Annotated[AsyncSession, Depends(get_session)]) -> UserResponse:
    result = await session.execute(select(User).where(User.id == user["sub"]))
    u = result.scalar_one_or_none()
    if u is None:
        raise AiosError(ErrorCode.E_AUTH_REQUIRED, "用户不存在", http_status=401)
    return UserResponse(
        id=u.id, username=u.username, role=u.role.value, created_at=u.created_at
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
