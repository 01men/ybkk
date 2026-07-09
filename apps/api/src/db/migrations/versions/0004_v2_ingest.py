"""add v2 ingest + llm + ontology mapping tables

Revision ID: 0004_v2_ingest
Revises: 0003_v1_core
Create Date: 2026-07-09
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_v2_ingest"
down_revision = "0003_v1_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False, index=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("minio_path", sa.String(512), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "succeeded", "failed", name="ingest_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("parsed_count", sa.Integer, server_default="0"),
        sa.Column("entities_count", sa.Integer, server_default="0"),
        sa.Column("relations_count", sa.Integer, server_default="0"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(64), nullable=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "llm_calls",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False, index=True),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("response_hash", sa.String(64), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False),
        sa.Column("output_tokens", sa.Integer, nullable=False),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("actor", sa.String(64), nullable=False, index=True),
        sa.Column("flow_id", sa.String(64), nullable=True, index=True),
        sa.Column("run_id", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "ontology_field_mappings",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("template_name", sa.String(128), nullable=False, index=True),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("target_kind", sa.String(32), nullable=False),
        sa.Column("field_map", JSONB, nullable=False),
        sa.Column("relations", JSONB, nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_table("ontology_field_mappings")
    op.drop_table("llm_calls")
    op.drop_table("ingest_jobs")
    op.execute("DROP TYPE IF EXISTS ingest_status")
