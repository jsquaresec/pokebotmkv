"""v71-v80 systems

Revision ID: 20260912_0009
Revises: 20260911_0008
"""
from alembic import op
import sqlalchemy as sa

revision = "20260912_0009"
down_revision = "20260911_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column in [
        sa.Column("trainer_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trainer_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("season_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bio", sa.String(240), nullable=False, server_default=""),
        sa.Column("selected_title", sa.String(80), nullable=False, server_default="Rookie Trainer"),
    ]:
        op.add_column("users", column)
    for column in [
        sa.Column("nickname", sa.String(40), nullable=True),
        sa.Column("nature", sa.String(30), nullable=False, server_default="Hardy"),
        sa.Column("ability", sa.String(80), nullable=False, server_default="Adaptability"),
        sa.Column("gender", sa.String(12), nullable=False, server_default="unknown"),
        sa.Column("favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("held_item", sa.String(50), nullable=True),
        sa.Column("moves_json", sa.Text(), nullable=False, server_default="[]"),
    ]:
        op.add_column("pokemon_instances", column)
    op.create_index("ix_pokemon_instances_favorite", "pokemon_instances", ["favorite"])

    op.create_table("pokedex_entries",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("discord_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("species", sa.String(100), nullable=False, index=True), sa.Column("seen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("caught_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("first_caught_at", sa.DateTime(), nullable=True), sa.UniqueConstraint("discord_id", "species", name="uq_pokedex_user_species"))
    op.create_table("achievements",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("discord_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("code", sa.String(80), nullable=False, index=True), sa.Column("unlocked_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("discord_id", "code", name="uq_achievement_user_code"))
    op.create_table("auctions",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("pokemon_id", sa.Integer(), sa.ForeignKey("pokemon_instances.id"), nullable=False, unique=True),
        sa.Column("seller_discord_id", sa.BigInteger(), nullable=False, index=True), sa.Column("highest_bidder_discord_id", sa.BigInteger(), nullable=True),
        sa.Column("starting_bid", sa.Integer(), nullable=False), sa.Column("current_bid", sa.Integer(), nullable=False),
        sa.Column("bid_increment", sa.Integer(), nullable=False, server_default="100"), sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
        sa.Column("ends_at", sa.DateTime(), nullable=False, index=True), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("auction_bids",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("auction_id", sa.Integer(), sa.ForeignKey("auctions.id"), nullable=False, index=True),
        sa.Column("bidder_discord_id", sa.BigInteger(), nullable=False, index=True), sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("friendships",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("requester_discord_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("addressee_discord_id", sa.BigInteger(), nullable=False, index=True), sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("requester_discord_id", "addressee_discord_id", name="uq_friend_pair"))
    op.create_table("season_reward_claims",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("discord_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("season_code", sa.String(50), nullable=False, index=True), sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=False), sa.UniqueConstraint("discord_id", "season_code", "tier", name="uq_season_claim"))
    op.create_table("idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("scope", sa.String(50), nullable=False, index=True),
        sa.Column("request_key", sa.String(100), nullable=False), sa.Column("actor_discord_id", sa.BigInteger(), nullable=False, index=True),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"), sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("scope", "request_key", name="uq_idempotency_scope_key"))


def downgrade() -> None:
    for table in ["idempotency_keys", "season_reward_claims", "friendships", "auction_bids", "auctions", "achievements", "pokedex_entries"]:
        op.drop_table(table)
    op.drop_index("ix_pokemon_instances_favorite", table_name="pokemon_instances")
    for column in ["moves_json", "held_item", "favorite", "gender", "ability", "nature", "nickname"]:
        op.drop_column("pokemon_instances", column)
    for column in ["selected_title", "bio", "season_xp", "trainer_xp", "trainer_level"]:
        op.drop_column("users", column)
