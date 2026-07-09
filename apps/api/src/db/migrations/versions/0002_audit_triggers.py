"""Alembic migration：0002_audit_triggers —— audit_log append-only 触发器。

参见 02-design-doc.md §6 安全考量 + TASK-060。
"""
"""add audit log append-only triggers

Revision ID: 0002_audit_triggers
Revises: 0001_init
Create Date: 2026-07-08
"""
from __future__ import annotations

from alembic import op

revision = "0002_audit_triggers"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 禁止 UPDATE
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_prevent_modify()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log is append-only (operation: %)', TG_OP
                USING ERRCODE = 'insufficient_privilege';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_no_update
        BEFORE UPDATE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION audit_log_prevent_modify();
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_log_no_delete
        BEFORE DELETE ON audit_log
        FOR EACH ROW
        EXECUTE FUNCTION audit_log_prevent_modify();
        """
    )
    # TRUNCATE 也禁
    op.execute(
        """
        CREATE TRIGGER audit_log_no_truncate
        BEFORE TRUNCATE ON audit_log
        FOR EACH STATEMENT
        EXECUTE FUNCTION audit_log_prevent_modify();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;")
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_delete ON audit_log;")
    op.execute("DROP TRIGGER IF EXISTS audit_log_no_truncate ON audit_log;")
    op.execute("DROP FUNCTION IF EXISTS audit_log_prevent_modify();")