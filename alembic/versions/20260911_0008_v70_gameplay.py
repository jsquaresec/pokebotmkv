"""v70 gameplay schema

Revision ID: 20260911_0008
Revises: 20260419_0007
"""
from alembic import op
import sqlalchemy as sa

revision = "20260911_0008"
down_revision = "20260419_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_inventory_owner_sku", "inventory_items", ["owner_discord_id", "sku"])
    for name, column in [
        ("dex_number", sa.Column("dex_number", sa.Integer(), nullable=False, server_default="0")),
        ("form", sa.Column("form", sa.String(80), nullable=False, server_default="Normal")),
        ("primary_type", sa.Column("primary_type", sa.String(30), nullable=False, server_default="normal")),
        ("secondary_type", sa.Column("secondary_type", sa.String(30), nullable=True)),
        ("experience", sa.Column("experience", sa.Integer(), nullable=False, server_default="0")),
        ("iv_hp", sa.Column("iv_hp", sa.Integer(), nullable=False, server_default="0")),
        ("iv_attack", sa.Column("iv_attack", sa.Integer(), nullable=False, server_default="0")),
        ("iv_defense", sa.Column("iv_defense", sa.Integer(), nullable=False, server_default="0")),
        ("iv_speed", sa.Column("iv_speed", sa.Integer(), nullable=False, server_default="0")),
        ("locked", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false())),
    ]:
        op.add_column("pokemon_instances", column)
    op.create_index("ix_pokemon_instances_dex_number", "pokemon_instances", ["dex_number"])
    op.create_index("ix_pokemon_instances_locked", "pokemon_instances", ["locked"])

    op.create_table(
        "wild_encounters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("guild_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("channel_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("species", sa.String(100), nullable=False, index=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("current_hp", sa.Integer(), nullable=False),
        sa.Column("max_hp", sa.Integer(), nullable=False),
        sa.Column("rarity", sa.String(30), nullable=False, server_default="common"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open", index=True),
        sa.Column("claimed_by_discord_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "market_listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pokemon_id", sa.Integer(), sa.ForeignKey("pokemon_instances.id"), nullable=False, unique=True),
        sa.Column("seller_discord_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("buyer_discord_id", sa.BigInteger(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("market_listings")
    op.drop_table("wild_encounters")
    op.drop_constraint("uq_inventory_owner_sku", "inventory_items", type_="unique")
    for index in ["ix_pokemon_instances_locked", "ix_pokemon_instances_dex_number"]:
        op.drop_index(index, table_name="pokemon_instances")
    for column in ["locked", "iv_speed", "iv_defense", "iv_attack", "iv_hp", "experience", "secondary_type", "primary_type", "form", "dex_number"]:
        op.drop_column("pokemon_instances", column)
