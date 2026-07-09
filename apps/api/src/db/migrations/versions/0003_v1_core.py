"""add users table + flows/flow_runs trigger fields

Revision ID: 0003_v1_core
Revises: 0002_audit_triggers
Create Date: 2026-07-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_v1_core"
down_revision = "0002_audit_triggers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users (V1 简化为单角色 admin)
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "operator", "viewer", name="user_role"),
            nullable=False,
            server_default="admin",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # flows: V1 新增 trigger 字段
    op.add_column("flows", sa.Column("trigger_type", sa.String(32), nullable=True))
    op.add_column("flows", sa.Column("trigger_config", JSONB, nullable=True))
    op.add_column("flows", sa.Column("temporal_workflow_id", sa.String(128), nullable=True))

    # flow_runs: V1 新增 step_results / actor / temporal_run_id / trigger_type
    op.add_column("flow_runs", sa.Column("trigger_type", sa.String(32), nullable=True))
    op.add_column("flow_runs", sa.Column("temporal_run_id", sa.String(128), nullable=True))
    op.add_column("flow_runs", sa.Column("step_results", JSONB, nullable=True))
    op.add_column("flow_runs", sa.Column("actor", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("flow_runs", "actor")
    op.drop_column("flow_runs", "step_results")
    op.drop_column("flow_runs", "temporal_run_id")
    op.drop_column("flow_runs", "trigger_type")
    op.drop_column("flows", "temporal_workflow_id")
    op.drop_column("flows", "trigger_config")
    op.drop_column("flows", "trigger_type")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role")
