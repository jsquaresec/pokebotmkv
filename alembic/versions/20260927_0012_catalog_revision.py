"""Track the species catalog used by owned Pokémon."""
from alembic import op
import sqlalchemy as sa

revision = "20260927_0012"
down_revision = "20260927_0011"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pokemon_instances", sa.Column("catalog_revision", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("pokemon_instances", "catalog_revision")
