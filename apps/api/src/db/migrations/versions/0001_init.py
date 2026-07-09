"""Alembic migration：0001_init —— 初始 6 张表（参见 02-design-doc.md §2.3）。

注意：
  - 包含 audit_log 的 hash_chain 字段
  - audit_log 的 append-only 触发器在 0002 中建
  - Neo4j 节点/关系在 ontology service 启动时建
"""
"""create initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-07-08
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # datasources
    op.create_table(
        "datasources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("type", sa.String(32), nullable=False, index=True),
        sa.Column("connection_json_encrypted", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "connecting", "connected", "failed", "disabled",
                name="datasource_status",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("last_check_at", sa.DateTime(timezone=True), nullable=True),
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

    # delivery_standards
    op.create_table(
        "delivery_standards",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("key", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, index=True),
        sa.Column("expr_json", JSONB, nullable=False),
        sa.Column("scope_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("built_in", sa.Boolean, nullable=False, server_default=sa.false(), index=True),
        sa.Column("tenant_id", sa.String(64), nullable=True, index=True),
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
    op.create_index("ix_standards_tenant_key", "delivery_standards", ["tenant_id", "key"])

    # scenarios
    op.create_table(
        "scenarios",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("key", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("industry", sa.String(32), nullable=False, index=True),
        sa.Column("default_standard_keys", JSONB, nullable=False, server_default="[]"),
        sa.Column("flow_template_json", JSONB, nullable=False),
        sa.Column("built_in", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text, nullable=True),
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

    # flows
    op.create_table(
        "flows",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("scenario_id", sa.String(64), sa.ForeignKey("scenarios.id"), nullable=False, index=True),
        sa.Column("datasource_bindings_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("standard_overrides_json", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "paused", "error", name="flow_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_by", sa.String(64), nullable=False, index=True),
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

    # flow_runs
    op.create_table(
        "flow_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("flow_id", sa.String(64), sa.ForeignKey("flows.id"), nullable=False, index=True),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "success", "failed", "cancelled", name="flow_run_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("output_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("audit_ref", sa.String(64), nullable=True, index=True),
    )
    op.create_index("ix_runs_flow_triggered", "flow_runs", ["flow_id", "triggered_at"])

    # audit_log（append-only；0002 加触发器）
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("actor", sa.String(64), nullable=False, index=True),
        sa.Column("action", sa.String(64), nullable=False, index=True),
        sa.Column("datasource_id", sa.String(64), nullable=True, index=True),
        sa.Column("standard_ref", sa.String(64), nullable=True),
        sa.Column("flow_id", sa.String(64), nullable=True, index=True),
        sa.Column("run_id", sa.String(64), nullable=True),
        sa.Column("payload_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("hash_chain", sa.String(128), nullable=False),
    )
    op.create_index("ix_audit_ts_desc", "audit_log", [sa.text("ts DESC")])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_index("ix_runs_flow_triggered", table_name="flow_runs")
    op.drop_table("flow_runs")
    op.drop_table("flows")
    op.drop_table("scenarios")
    op.drop_index("ix_standards_tenant_key", table_name="delivery_standards")
    op.drop_table("delivery_standards")
    op.drop_table("datasources")
    op.execute("DROP TYPE IF EXISTS flow_run_status")
    op.execute("DROP TYPE IF EXISTS flow_status")
    op.execute("DROP TYPE IF EXISTS datasource_status")