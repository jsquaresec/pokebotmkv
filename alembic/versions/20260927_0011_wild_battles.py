"""Persist wild battle turns and party state on each encounter."""
from alembic import op
import sqlalchemy as sa

revision = "20260927_0011"
down_revision = "20260912_0010"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("wild_encounters", sa.Column("battle_state_json", sa.Text(), nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("wild_encounters", "battle_state_json")
