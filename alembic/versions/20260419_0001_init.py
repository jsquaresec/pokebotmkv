"""initial schema

Revision ID: 20260419_0001
Revises:
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260419_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("discord_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_discord_id", "users", ["discord_id"], unique=True)

    op.create_table(
        "pokemon_instances",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("species", sa.String(length=100), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("current_hp", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("max_hp", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("attack", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("defense", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("speed", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("shiny", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_pokemon_instances_owner_id", "pokemon_instances", ["owner_id"], unique=False)
    op.create_index("ix_pokemon_instances_species", "pokemon_instances", ["species"], unique=False)

    op.create_table(
        "party_slots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pokemon_id", sa.Integer(), sa.ForeignKey("pokemon_instances.id"), nullable=False),
        sa.Column("slot_index", sa.Integer(), nullable=False),
        sa.UniqueConstraint("owner_id", "slot_index", name="uq_party_owner_slot"),
    )

    op.create_table(
        "queue_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("discord_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("discord_id", name="uq_queue_discord_id"),
    )
    op.create_index("ix_queue_entries_discord_id", "queue_entries", ["discord_id"], unique=False)

    op.create_table(
        "active_battles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("battle_type", sa.String(length=50), nullable=False),
        sa.Column("player_one_discord_id", sa.Integer(), nullable=False),
        sa.Column("player_two_discord_id", sa.Integer(), nullable=False),
        sa.Column("state_json", sa.Text(), nullable=False),
        sa.Column("finished", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_active_battles_battle_type", "active_battles", ["battle_type"], unique=False)
    op.create_index("ix_active_battles_player_one_discord_id", "active_battles", ["player_one_discord_id"], unique=False)
    op.create_index("ix_active_battles_player_two_discord_id", "active_battles", ["player_two_discord_id"], unique=False)

    op.create_table(
        "ranked_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("losses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("owner_id", name="uq_ranked_owner"),
    )
    op.create_index("ix_ranked_profiles_owner_id", "ranked_profiles", ["owner_id"], unique=False)

    op.create_table(
        "battle_replays",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("battle_id", sa.Integer(), nullable=False),
        sa.Column("battle_type", sa.String(length=50), nullable=False),
        sa.Column("replay_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_battle_replays_battle_id", "battle_replays", ["battle_id"], unique=False)
    op.create_index("ix_battle_replays_battle_type", "battle_replays", ["battle_type"], unique=False)

    op.create_table(
        "rulesets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_ranked_legal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_rulesets_name", "rulesets", ["name"])

    op.create_table(
        "cosmetics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("cosmetic_type", sa.String(length=50), nullable=False),
        sa.Column("rarity", sa.String(length=30), nullable=False, server_default="common"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_cosmetics_name", "cosmetics", ["name"])
    op.create_index("ix_cosmetics_cosmetic_type", "cosmetics", ["cosmetic_type"], unique=False)

    op.create_table(
        "live_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint("uq_live_events_name", "live_events", ["name"])
    op.create_index("ix_live_events_event_type", "live_events", ["event_type"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_live_events_event_type", table_name="live_events")
    op.drop_table("live_events")
    op.drop_index("ix_cosmetics_cosmetic_type", table_name="cosmetics")
    op.drop_table("cosmetics")
    op.drop_table("rulesets")
    op.drop_index("ix_battle_replays_battle_type", table_name="battle_replays")
    op.drop_index("ix_battle_replays_battle_id", table_name="battle_replays")
    op.drop_table("battle_replays")
    op.drop_index("ix_ranked_profiles_owner_id", table_name="ranked_profiles")
    op.drop_table("ranked_profiles")
    op.drop_index("ix_active_battles_player_two_discord_id", table_name="active_battles")
    op.drop_index("ix_active_battles_player_one_discord_id", table_name="active_battles")
    op.drop_index("ix_active_battles_battle_type", table_name="active_battles")
    op.drop_table("active_battles")
    op.drop_index("ix_queue_entries_discord_id", table_name="queue_entries")
    op.drop_table("queue_entries")
    op.drop_table("party_slots")
    op.drop_index("ix_pokemon_instances_species", table_name="pokemon_instances")
    op.drop_index("ix_pokemon_instances_owner_id", table_name="pokemon_instances")
    op.drop_table("pokemon_instances")
    op.drop_index("ix_users_discord_id", table_name="users")
    op.drop_table("users")
