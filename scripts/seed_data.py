import asyncio
from sqlalchemy import select
from core.database import SessionLocal, init_models
from models.ruleset import Ruleset
from models.cosmetic import Cosmetic
from models.live_event import LiveEvent

RULESETS = [
    {
        "name": "Standard",
        "description": "Default ranked-legal ruleset",
        "config_json": '{"max_team_size": 6, "items_allowed": true}',
        "is_ranked_legal": True,
    },
    {
        "name": "No Items",
        "description": "Battle ruleset with battle items disabled",
        "config_json": '{"max_team_size": 6, "items_allowed": false}',
        "is_ranked_legal": False,
    },
]

COSMETICS = [
    {"name": "Classic Trainer Border", "cosmetic_type": "profile_border", "rarity": "common"},
    {"name": "Elite Trainer Border", "cosmetic_type": "profile_border", "rarity": "rare"},
    {"name": "Champion Flair", "cosmetic_type": "title_badge", "rarity": "epic"},
]

LIVE_EVENTS = [
    {"name": "Launch Week Bonus", "event_type": "login_bonus", "config_json": '{"bonus": "100 coins"}'},
    {"name": "Catch Rush", "event_type": "spawn_boost", "config_json": '{"spawn_multiplier": 2}'},
]

async def ensure_ruleset(session, item):
    existing = await session.execute(select(Ruleset).where(Ruleset.name == item["name"]))
    if existing.scalar_one_or_none() is None:
        session.add(Ruleset(**item))

async def ensure_cosmetic(session, item):
    existing = await session.execute(select(Cosmetic).where(Cosmetic.name == item["name"]))
    if existing.scalar_one_or_none() is None:
        session.add(Cosmetic(
            name=item["name"],
            cosmetic_type=item["cosmetic_type"],
            rarity=item["rarity"],
            is_active=True,
        ))

async def ensure_live_event(session, item):
    existing = await session.execute(select(LiveEvent).where(LiveEvent.name == item["name"]))
    if existing.scalar_one_or_none() is None:
        session.add(LiveEvent(
            name=item["name"],
            event_type=item["event_type"],
            config_json=item["config_json"],
            is_active=True,
        ))

async def main():
    await init_models()
    async with SessionLocal() as session:
        for item in RULESETS:
            await ensure_ruleset(session, item)
        for item in COSMETICS:
            await ensure_cosmetic(session, item)
        for item in LIVE_EVENTS:
            await ensure_live_event(session, item)
        await session.commit()
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(main())
