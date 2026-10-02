"""add inventory and trade

Revision ID: 20260419_0006
Revises: 20260419_0005
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0006"
down_revision = "20260419_0005"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "inventory_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_discord_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_inventory_items_owner_discord_id", "inventory_items", ["owner_discord_id"], unique=False)
    op.create_index("ix_inventory_items_sku", "inventory_items", ["sku"], unique=False)

    op.create_table(
        "trade_offers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("from_discord_id", sa.Integer(), nullable=False),
        sa.Column("to_discord_id", sa.Integer(), nullable=False),
        sa.Column("offered_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("requested_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_trade_offers_from_discord_id", "trade_offers", ["from_discord_id"], unique=False)
    op.create_index("ix_trade_offers_to_discord_id", "trade_offers", ["to_discord_id"], unique=False)
    op.create_index("ix_trade_offers_status", "trade_offers", ["status"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_trade_offers_status", table_name="trade_offers")
    op.drop_index("ix_trade_offers_to_discord_id", table_name="trade_offers")
    op.drop_index("ix_trade_offers_from_discord_id", table_name="trade_offers")
    op.drop_table("trade_offers")
    op.drop_index("ix_inventory_items_sku", table_name="inventory_items")
    op.drop_index("ix_inventory_items_owner_discord_id", table_name="inventory_items")
    op.drop_table("inventory_items")
