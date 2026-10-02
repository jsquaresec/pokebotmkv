"""add daily rewards and quests

Revision ID: 20260419_0007
Revises: 20260419_0006
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0007"
down_revision = "20260419_0006"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "daily_reward_claims",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("recipient_discord_id", sa.Integer(), nullable=False),
        sa.Column("streak_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_daily_reward_claims_recipient_discord_id", "daily_reward_claims", ["recipient_discord_id"], unique=False)

    op.create_table(
        "quest_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("recipient_discord_id", sa.Integer(), nullable=False),
        sa.Column("quest_code", sa.String(length=50), nullable=False),
        sa.Column("progress_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_quest_progress_recipient_discord_id", "quest_progress", ["recipient_discord_id"], unique=False)
    op.create_index("ix_quest_progress_quest_code", "quest_progress", ["quest_code"], unique=False)
    op.create_index("ix_quest_progress_status", "quest_progress", ["status"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_quest_progress_status", table_name="quest_progress")
    op.drop_index("ix_quest_progress_quest_code", table_name="quest_progress")
    op.drop_index("ix_quest_progress_recipient_discord_id", table_name="quest_progress")
    op.drop_table("quest_progress")
    op.drop_index("ix_daily_reward_claims_recipient_discord_id", table_name="daily_reward_claims")
    op.drop_table("daily_reward_claims")
