"""aios_api.middleware.rbac —— V3 RBAC 权限校验。"""
from __future__ import annotations

# V3 内置权限点（与 migration 0005 _seed_permissions 同步）
ALL_PERMISSIONS: tuple[str, ...] = (
    # datasource
    "datasource.read", "datasource.write", "datasource.delete",
    # scenario
    "scenario.read", "scenario.write", "scenario.delete",
    # flow
    "flow.read", "flow.write", "flow.delete", "flow.execute",
    # ingest
    "ingest.execute", "ingest.read",
    # ontology
    "ontology.read", "ontology.write",
    # llm
    "llm.test", "llm.read",
    # audit
    "audit.read",
    # org
    "org.read", "org.write", "org.delete", "org.invite", "org.manage_members",
    # user
    "user.read", "user.write", "user.delete",
    # monitoring
    "monitoring.read",
    # system
    "system.manage",
)

# 角色级别
ROLE_LEVEL: dict[str, int] = {
    "admin": 4,
    "engineer": 3,
    "operator": 2,
    "viewer": 1,
}

# 角色权限矩阵（与 migration 0005 同步）
ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "admin": frozenset(ALL_PERMISSIONS),
    "engineer": frozenset({
        "datasource.read", "datasource.write",
        "scenario.read", "scenario.write",
        "flow.read", "flow.write", "flow.execute",
        "ingest.execute", "ingest.read",
        "ontology.read", "ontology.write",
        "llm.test", "llm.read",
        "audit.read",
        "monitoring.read",
    }),
    "operator": frozenset({
        "datasource.read",
        "scenario.read",
        "flow.read", "flow.execute",
        "ingest.execute",
        "ontology.read",
        "llm.read",
    }),
    "viewer": frozenset({
        "datasource.read",
        "scenario.read",
        "flow.read",
        "ontology.read",
        "audit.read",
        "monitoring.read",
    }),
}


def has_permission(role_key: str, perm: str) -> bool:
    """判定角色是否有某权限。"""
    if role_key not in ROLE_PERMISSIONS:
        return False
    return perm in ROLE_PERMISSIONS[role_key]


def permissions_for(role_key: str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role_key, frozenset())


__all__ = [
    "ALL_PERMISSIONS",
    "ROLE_LEVEL",
    "ROLE_PERMISSIONS",
    "has_permission",
    "permissions_for",
]
