"""add reward claims

Revision ID: 20260419_0005
Revises: 20260419_0004
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0005"
down_revision = "20260419_0004"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "reward_claims",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("recipient_discord_id", sa.Integer(), nullable=False),
        sa.Column("reward_type", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("related_battle_id", sa.Integer(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reward_claims_recipient_discord_id", "reward_claims", ["recipient_discord_id"], unique=False)
    op.create_index("ix_reward_claims_reward_type", "reward_claims", ["reward_type"], unique=False)
    op.create_index("ix_reward_claims_related_battle_id", "reward_claims", ["related_battle_id"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_reward_claims_related_battle_id", table_name="reward_claims")
    op.drop_index("ix_reward_claims_reward_type", table_name="reward_claims")
    op.drop_index("ix_reward_claims_recipient_discord_id", table_name="reward_claims")
    op.drop_table("reward_claims")
