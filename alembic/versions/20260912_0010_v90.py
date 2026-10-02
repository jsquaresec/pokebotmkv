"""Allow relisting sold Pokémon while retaining historical records."""
from alembic import op
import sqlalchemy as sa

revision = "20260912_0010"
down_revision = "20260912_0009"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("active_battles", "player_one_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("active_battles", "player_two_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("audit_logs", "actor_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("daily_reward_claims", "recipient_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("inventory_items", "owner_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("notification_deliveries", "recipient_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("quest_progress", "recipient_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("queue_entries", "discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("reward_claims", "recipient_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("trade_offers", "from_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column("trade_offers", "to_discord_id", type_=sa.BigInteger(), existing_type=sa.Integer())
    op.drop_constraint("market_listings_pokemon_id_key", "market_listings", type_="unique")
    op.drop_constraint("auctions_pokemon_id_key", "auctions", type_="unique")
    op.create_index("uq_market_active_pokemon", "market_listings", ["pokemon_id"], unique=True,
                    postgresql_where=__import__('sqlalchemy').text("status = 'active'"))
    op.create_index("uq_auction_active_pokemon", "auctions", ["pokemon_id"], unique=True,
                    postgresql_where=__import__('sqlalchemy').text("status = 'active'"))


def downgrade():
    raise RuntimeError("Irreversible automatically: historical relistings may duplicate Pokémon IDs. Restore a reviewed backup.")
