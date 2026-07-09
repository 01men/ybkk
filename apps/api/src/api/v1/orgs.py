"""aios_api.api.v1.orgs —— V3 多租户组织 CRUD + 成员管理 + 切换。

V4 改造：/me 已经在 token 里带 perms；本路由主要职责：
  - 列出我的组织（基于 OrgMember 反查）
  - 创建组织（admin-only，自动把当前用户加为 admin）
  - 切换组织（返回带新 org_id/role_key 的 JWT，让前端覆盖 localStorage）
  - 成员邀请/改角色/移除
"""
from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...auth import user_to_jwt
from ...db import get_session
from ...errors import AiosError, ErrorCode
from ...middleware.auth import CurrentUser
from ...middleware.rbac import has_permission
from ...models import Org, OrgMember, User

router = APIRouter(prefix="/orgs", tags=["orgs"])


# -----------------------------------------------------------------------------
# Pydantic
# -----------------------------------------------------------------------------


class OrgCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$")


class OrgItem(BaseModel):
    id: str
    name: str
    slug: str
    role_key: str  # 当前用户在该组织的角色
    member_count: int = 1
    created_at: str  # ISO 字符串


class SwitchResponse(BaseModel):
    token: str
    org_id: str
    role_key: str


class MemberItem(BaseModel):
    user_id: str
    username: str
    role_key: str
    joined_at: str


class InviteRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    role_key: str = Field(..., pattern=r"^(admin|engineer|operator|viewer)$")


class UpdateRoleRequest(BaseModel):
    role_key: str = Field(..., pattern=r"^(admin|engineer|operator|viewer)$")


# -----------------------------------------------------------------------------
# 依赖：当前用户必带 org_id/role_key（V4 强制重新签发后必然有）
# -----------------------------------------------------------------------------


def _ctx(user: dict) -> tuple[str, str]:
    org_id = user.get("org_id", "")
    role_key = user.get("role_key", "")
    if not org_id or not role_key:
        raise AiosError(
            ErrorCode.E_AUTH_TOKEN_INVALID,
            "token 缺少 org_id/role_key（请重新登录）",
            http_status=401,
        )
    return org_id, role_key


def _require_perm(user: dict, perm: str) -> None:
    role_key = user.get("role_key", "")
    if not has_permission(role_key, perm):
        raise AiosError(
            ErrorCode.E_AUTH_FORBIDDEN,
            f"缺少权限: {perm}",
            http_status=403,
        )


# -----------------------------------------------------------------------------
# 端点
# -----------------------------------------------------------------------------


@router.get("", summary="列出我的组织")
async def list_my_orgs(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[OrgItem]:
    result = await session.execute(
        select(Org, OrgMember)
        .join(OrgMember, OrgMember.org_id == Org.id)
        .where(OrgMember.user_id == user["sub"])
        .order_by(OrgMember.joined_at.asc())
    )
    items: list[OrgItem] = []
    for org, member in result.all():
        cnt_r = await session.execute(
            select(OrgMember).where(OrgMember.org_id == org.id)
        )
        items.append(
            OrgItem(
                id=org.id,
                name=org.name,
                slug=org.slug,
                role_key=member.role_key,
                member_count=len(cnt_r.scalars().all()),
                created_at=org.created_at.isoformat(),
            )
        )
    return items


@router.post("", summary="创建组织")
async def create_org(
    body: OrgCreateRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrgItem:
    """V4: 需要 org.write 权限（默认 admin only）。自动把当前用户加为 admin。"""
    _require_perm(user, "org.write")
    new_org = Org(id=str(uuid4()), name=body.name, slug=body.slug)
    session.add(new_org)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise AiosError(
            ErrorCode.E_ORG_CONFLICT,
            f"slug 已存在: {body.slug}",
            http_status=409,
        )
    session.add(
        OrgMember(org_id=new_org.id, user_id=user["sub"], role_key="admin")
    )
    await session.commit()
    return OrgItem(
        id=new_org.id,
        name=new_org.name,
        slug=new_org.slug,
        role_key="admin",
        member_count=1,
        created_at=new_org.created_at.isoformat(),
    )


@router.post("/{org_id}/switch", summary="切换组织（返回新 token）")
async def switch_org(
    org_id: str,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SwitchResponse:
    """V4: 校验当前用户是 org_id 的成员 → 签新 JWT（带新 org_id/role_key/perms/ver）。"""
    member_r = await session.execute(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == user["sub"],
        )
    )
    member = member_r.scalar_one_or_none()
    if member is None:
        raise AiosError(
            ErrorCode.E_AUTH_FORBIDDEN,
            "你不是该组织成员",
            http_status=403,
        )
    user_r = await session.execute(select(User).where(User.id == user["sub"]))
    u = user_r.scalar_one()
    new_token = user_to_jwt(u, org_id=org_id, role_key=member.role_key)
    return SwitchResponse(token=new_token, org_id=org_id, role_key=member.role_key)


@router.get("/{org_id}/members", summary="列出组织成员")
async def list_members(
    org_id: str,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[MemberItem]:
    _ctx(user)  # 强校验 token 有 org 上下文
    result = await session.execute(
        select(OrgMember, User)
        .join(User, User.id == OrgMember.user_id)
        .where(OrgMember.org_id == org_id)
        .order_by(OrgMember.joined_at.asc())
    )
    return [
        MemberItem(
            user_id=u.id,
            username=u.username,
            role_key=m.role_key,
            joined_at=m.joined_at.isoformat(),
        )
        for m, u in result.all()
    ]


@router.post("/{org_id}/members", summary="邀请成员")
async def invite_member(
    org_id: str,
    body: InviteRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MemberItem:
    _require_perm(user, "org.invite")
    # 校验 user 存在
    u_r = await session.execute(select(User).where(User.id == body.user_id))
    u = u_r.scalar_one_or_none()
    if u is None:
        raise AiosError(ErrorCode.E_NOT_FOUND, "用户不存在", http_status=404)
    # 已加入？
    m_r = await session.execute(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == body.user_id,
        )
    )
    if m_r.scalar_one_or_none() is not None:
        raise AiosError(
            ErrorCode.E_ORG_CONFLICT,
            "用户已是该组织成员",
            http_status=409,
        )
    m = OrgMember(org_id=org_id, user_id=body.user_id, role_key=body.role_key)
    session.add(m)
    await session.commit()
    return MemberItem(
        user_id=u.id,
        username=u.username,
        role_key=body.role_key,
        joined_at=m.joined_at.isoformat(),
    )


@router.patch("/{org_id}/members/{user_id}", summary="改成员角色")
async def update_member_role(
    org_id: str,
    user_id: str,
    body: UpdateRoleRequest,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MemberItem:
    _require_perm(user, "org.manage_members")
    m_r = await session.execute(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == user_id,
        )
    )
    m = m_r.scalar_one_or_none()
    if m is None:
        raise AiosError(ErrorCode.E_NOT_FOUND, "成员不存在", http_status=404)
    m.role_key = body.role_key
    await session.commit()
    u_r = await session.execute(select(User).where(User.id == user_id))
    u = u_r.scalar_one()
    return MemberItem(
        user_id=u.id,
        username=u.username,
        role_key=body.role_key,
        joined_at=m.joined_at.isoformat(),
    )


@router.delete("/{org_id}/members/{user_id}", summary="移除成员")
async def remove_member(
    org_id: str,
    user_id: str,
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    _require_perm(user, "org.manage_members")
    await session.execute(
        delete(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == user_id,
        )
    )
    await session.commit()
    return {"ok": True}


__all__ = ["router"]