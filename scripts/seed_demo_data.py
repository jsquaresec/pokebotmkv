import asyncio
from sqlalchemy import select
from core.database import SessionLocal, init_models
from models.user import User
from models.pokemon import PokemonInstance
from models.ranked_profile import RankedProfile

DEMO_USERS = [
    {"discord_id": 900001, "username": "DemoRed"},
    {"discord_id": 900002, "username": "DemoBlue"},
]

DEMO_POKEMON = [
    {"owner_discord_id": 900001, "species": "Pikachu", "level": 8, "current_hp": 26, "max_hp": 26, "attack": 14, "defense": 8, "speed": 16, "shiny": False},
    {"owner_discord_id": 900002, "species": "Bulbasaur", "level": 8, "current_hp": 28, "max_hp": 28, "attack": 11, "defense": 11, "speed": 9, "shiny": False},
]

async def main():
    await init_models()
    async with SessionLocal() as session:
        created_users = {}

        for item in DEMO_USERS:
            existing = await session.execute(select(User).where(User.discord_id == item["discord_id"]))
            user = existing.scalar_one_or_none()
            if user is None:
                user = User(discord_id=item["discord_id"], username=item["username"], balance=5000)
                session.add(user)
                await session.flush()
            created_users[item["discord_id"]] = user

            ranked = await session.execute(select(RankedProfile).where(RankedProfile.owner_id == user.id))
            if ranked.scalar_one_or_none() is None:
                session.add(RankedProfile(owner_id=user.id, rating=1000, wins=0, losses=0))

        await session.flush()

        for item in DEMO_POKEMON:
            owner = created_users[item["owner_discord_id"]]
            existing = await session.execute(
                select(PokemonInstance).where(
                    PokemonInstance.owner_id == owner.id,
                    PokemonInstance.species == item["species"],
                    PokemonInstance.level == item["level"],
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(PokemonInstance(
                    owner_id=owner.id,
                    species=item["species"],
                    level=item["level"],
                    current_hp=item["current_hp"],
                    max_hp=item["max_hp"],
                    attack=item["attack"],
                    defense=item["defense"],
                    speed=item["speed"],
                    shiny=item["shiny"],
                ))

        await session.commit()
    print("Demo seed complete.")

if __name__ == "__main__":
    asyncio.run(main())
