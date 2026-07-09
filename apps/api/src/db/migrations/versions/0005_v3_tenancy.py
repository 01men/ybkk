"""V3 多租户 + RBAC + 业务表 org_id 列

Revision ID: 0005_v3_tenancy
Revises: 0004_v2_ingest
Create Date: 2026-07-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_v3_tenancy"
down_revision = "0004_v2_ingest"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----- 多租户 -----
    op.create_table(
        "orgs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "org_members",
        sa.Column("org_id", sa.String(64), sa.ForeignKey("orgs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_key", sa.String(32), nullable=False, index=True),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # ----- RBAC -----
    op.create_table(
        "roles",
        sa.Column("key", sa.String(32), primary_key=True),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("level", sa.Integer, nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("key", sa.String(64), primary_key=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_key", sa.String(32), sa.ForeignKey("roles.key", ondelete="CASCADE"), primary_key=True),
        sa.Column("perm_key", sa.String(64), sa.ForeignKey("permissions.key", ondelete="CASCADE"), primary_key=True),
    )

    # 内置 4 角色
    op.bulk_insert(
        sa.table(
            "roles",
            sa.column("key", sa.String),
            sa.column("label", sa.String),
            sa.column("level", sa.Integer),
        ),
        [
            {"key": "admin", "label": "管理员", "level": 4},
            {"key": "engineer", "label": "工程师", "level": 3},
            {"key": "operator", "label": "操作员", "level": 2},
            {"key": "viewer", "label": "只读", "level": 1},
        ],
    )

    # 内置 30 权限点 + role_permissions
    _seed_permissions()

    # ----- 业务表加 org_id -----
    for table in (
        "datasources",
        "scenarios",
        "flows",
        "flow_runs",
        "audit_log",
        "ingest_jobs",
        "llm_calls",
    ):
        op.add_column(table, sa.Column("org_id", sa.String(64), nullable=True))
        op.create_index(f"ix_{table}_org_id", table, ["org_id"])


def downgrade() -> None:
    for table in (
        "llm_calls",
        "ingest_jobs",
        "audit_log",
        "flow_runs",
        "flows",
        "scenarios",
        "datasources",
    ):
        op.drop_index(f"ix_{table}_org_id", table_name=table)
        op.drop_column(table, "org_id")

    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("org_members")
    op.drop_table("orgs")


def _seed_permissions() -> None:
    """V3 种子权限点。"""
    perms = [
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
        # org (admin 专属)
        "org.read", "org.write", "org.delete", "org.invite", "org.manage_members",
        # user
        "user.read", "user.write", "user.delete",
        # monitoring
        "monitoring.read",
        # system
        "system.manage",
    ]
    op.bulk_insert(
        sa.table("permissions", sa.column("key", sa.String)),
        [{"key": p} for p in perms],
    )

    # 角色权限矩阵
    matrix = {
        "admin": perms,  # 全
        "engineer": [
            "datasource.read", "datasource.write",
            "scenario.read", "scenario.write",
            "flow.read", "flow.write", "flow.execute",
            "ingest.execute", "ingest.read",
            "ontology.read", "ontology.write",
            "llm.test", "llm.read",
            "audit.read",
            "monitoring.read",
        ],
        "operator": [
            "datasource.read",
            "scenario.read",
            "flow.read", "flow.execute",
            "ingest.execute",
            "ontology.read",
            "llm.read",
        ],
        "viewer": [
            "datasource.read",
            "scenario.read",
            "flow.read",
            "ontology.read",
            "audit.read",
            "monitoring.read",
        ],
    }
    rows = []
    for role_key, perm_keys in matrix.items():
        for pk in perm_keys:
            rows.append({"role_key": role_key, "perm_key": pk})
    op.bulk_insert(
        sa.table(
            "role_permissions",
            sa.column("role_key", sa.String),
            sa.column("perm_key", sa.String),
        ),
        rows,
    )
