"""add audit logs

Revision ID: 20260419_0002
Revises: 20260419_0001
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0002"
down_revision = "20260419_0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("actor_discord_id", sa.Integer(), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"], unique=False)
    op.create_index("ix_audit_logs_actor_discord_id", "audit_logs", ["actor_discord_id"], unique=False)
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_audit_logs_target_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_discord_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_table("audit_logs")
