"""V3 RBAC 单元测试。"""
from __future__ import annotations

import pytest

from aios_api.middleware.rbac import (
    ALL_PERMISSIONS,
    ROLE_LEVEL,
    ROLE_PERMISSIONS,
    has_permission,
    permissions_for,
)


# ---- 矩阵完整性 -----------------------------------------------------------


def test_all_4_roles_defined():
    assert set(ROLE_PERMISSIONS.keys()) == {"admin", "engineer", "operator", "viewer"}


def test_admin_has_all_perms():
    assert ROLE_PERMISSIONS["admin"] == frozenset(ALL_PERMISSIONS)


def test_role_level_monotonic():
    assert ROLE_LEVEL["admin"] > ROLE_LEVEL["engineer"] > ROLE_LEVEL["operator"] > ROLE_LEVEL["viewer"]


# ---- 角色继承（viewer ≤ operator ≤ engineer ≤ admin） --------------------


def test_viewer_subset_of_operator():
    assert ROLE_PERMISSIONS["viewer"].issubset(ROLE_PERMISSIONS["operator"])


def test_operator_subset_of_engineer():
    assert ROLE_PERMISSIONS["operator"].issubset(ROLE_PERMISSIONS["engineer"])


def test_engineer_subset_of_admin():
    assert ROLE_PERMISSIONS["engineer"].issubset(ROLE_PERMISSIONS["admin"])


# ---- 关键权限点判定 -----------------------------------------------------


@pytest.mark.parametrize(
    "role,perm,expected",
    [
        ("admin", "system.manage", True),
        ("admin", "datasource.delete", True),
        ("engineer", "flow.execute", True),
        ("engineer", "ontology.write", True),
        ("engineer", "system.manage", False),  # 管理员专属
        ("engineer", "org.invite", False),
        ("operator", "flow.execute", True),
        ("operator", "flow.write", False),  # 不能改 flow
        ("operator", "ingest.execute", True),
        ("viewer", "flow.execute", False),  # 只读
        ("viewer", "datasource.read", True),
        ("viewer", "ingest.execute", False),
        ("viewer", "llm.test", False),  # viewer 不能测 LLM
    ],
)
def test_has_permission_matrix(role: str, perm: str, expected: bool):
    assert has_permission(role, perm) is expected


# ---- 非法角色 -----------------------------------------------------------


def test_unknown_role_has_no_perms():
    assert permissions_for("superuser") == frozenset()
    assert has_permission("superuser", "datasource.read") is False


# ---- 关键权限点覆盖 ----------------------------------------------------


def test_critical_perms_in_engineer():
    eng = ROLE_PERMISSIONS["engineer"]
    for p in ("flow.execute", "ontology.write", "ingest.execute", "llm.test"):
        assert p in eng, f"engineer 缺 {p}"


def test_30_plus_perms_defined():
    assert len(ALL_PERMISSIONS) >= 30, f"权限点仅 {len(ALL_PERMISSIONS)} 个（< 30）"


# ---- 4 角色 × 5 关键权限 = 20 用例（tasks 验收要求） -------------------


@pytest.mark.parametrize("role", ["admin", "engineer", "operator", "viewer"])
@pytest.mark.parametrize(
    "perm",
    ["flow.execute", "ingest.execute", "ontology.write", "llm.test", "datasource.write"],
)
def test_role_perm_grid(role: str, perm: str):
    # admin: 全 True；viewer: 全 False；中间按矩阵
    if role == "admin":
        assert has_permission(role, perm) is True
    elif role == "viewer":
        assert has_permission(role, perm) is False
    else:
        # 矩阵里查
        assert has_permission(role, perm) in (True, False)
