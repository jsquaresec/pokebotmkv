"""add notification deliveries

Revision ID: 20260419_0003
Revises: 20260419_0002
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0003"
down_revision = "20260419_0002"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("recipient_discord_id", sa.Integer(), nullable=False),
        sa.Column("related_battle_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notification_deliveries_event_type", "notification_deliveries", ["event_type"], unique=False)
    op.create_index("ix_notification_deliveries_recipient_discord_id", "notification_deliveries", ["recipient_discord_id"], unique=False)
    op.create_index("ix_notification_deliveries_related_battle_id", "notification_deliveries", ["related_battle_id"], unique=False)
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_related_battle_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_recipient_discord_id", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_event_type", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
