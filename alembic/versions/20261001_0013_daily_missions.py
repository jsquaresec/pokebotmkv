"""Persistent daily missions and item rewards."""
from alembic import op
import sqlalchemy as sa
revision = '20261001_0013'
down_revision = '20260927_0012'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('daily_missions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('discord_id', sa.BigInteger(), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('code', sa.String(30), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('reward_sku', sa.String(50), nullable=False),
        sa.Column('reward_quantity', sa.Integer(), nullable=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('discord_id', 'day', 'code', name='uq_daily_mission_user_day_code'))
    op.create_index('ix_daily_missions_discord_id', 'daily_missions', ['discord_id'])

def downgrade():
    op.drop_table('daily_missions')
