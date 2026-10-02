"""add notification retry count

Revision ID: 20260419_0004
Revises: 20260419_0003
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0004"
down_revision = "20260419_0003"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("notification_deliveries", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))

def downgrade() -> None:
    op.drop_column("notification_deliveries", "retry_count")
