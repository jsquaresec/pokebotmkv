import random
import json
from datetime import datetime, timedelta
from models.pokemon import PokemonInstance
from models.party import PartySlot
from models.user import User
from sqlalchemy import select
from repositories.wild_encounters import WildEncounterRepository
from services.content_registry_v70 import ContentRegistryV70
from services.pokemon_traits_service import PokemonTraitsService
from services.moveset_v80_service import MovesetV80Service
from repositories.pokedex import PokedexRepository
from services.trainer_progression_service import TrainerProgressionService
from config import settings


CATCH_GOLD_REWARD = 500

BALLS = {
    "poke_ball": 1.0,
    "great_ball": 1.5,
    "ultra_ball": 2.0,
    "master_ball": 999.0,
}


class EncounterV70Service:
    LEVEL_VARIATION = 2
    DEFAULT_LEADER_LEVEL = 5

    def __init__(self, session, registry: ContentRegistryV70 | None = None, rng=None):
        self.session = session
        self.repo = WildEncounterRepository(session)
        self.registry = registry or ContentRegistryV70()
        self.rng = rng or random.Random()

    async def spawn_level(self, trainer_discord_id: int | None = None) -> int:
        leader_level = None
        if trainer_discord_id is not None:
            leader_level = (await self.session.execute(
                select(PokemonInstance.level)
                .join(PartySlot, PartySlot.pokemon_id == PokemonInstance.id)
                .join(User, User.id == PartySlot.owner_id)
                .where(User.discord_id == trainer_discord_id, PokemonInstance.owner_id == User.id)
                .order_by(PartySlot.slot_index.asc()).limit(1)
            )).scalar_one_or_none()
        center = max(1, min(100, leader_level if leader_level is not None else self.DEFAULT_LEADER_LEVEL))
        return self.rng.randint(max(1, center - self.LEVEL_VARIATION), min(100, center + self.LEVEL_VARIATION))

    async def spawn(self, guild_id: int, channel_id: int, trainer_discord_id: int | None = None):
        name = self.rng.choice(self.registry.all_species())
        species = self.registry.species(name)
        level = await self.spawn_level(trainer_discord_id)
        hp = species["base_hp"] + level * 2
        rarity = species['rarity']
        return await self.repo.create(
            guild_id=guild_id, channel_id=channel_id, species=name, level=level,
            current_hp=hp, max_hp=hp, rarity=rarity,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.encounter_ttl_seconds),
        )

    def catch_probability(self, encounter, ball_sku: str, current_hp: int | None = None) -> float:
        if ball_sku not in BALLS:
            raise ValueError("Unknown Poké Ball.")
        if ball_sku == "master_ball":
            return 1.0
        species = self.registry.species(encounter.species)
        # Reward weakening: 0.35x at full HP, increasing toward 2x near zero HP.
        hp = encounter.current_hp if current_hp is None else current_hp
        hp_ratio = max(0.0, min(1.0, hp / max(1, encounter.max_hp)))
        hp_factor = 0.35 + 1.65 * (1.0 - hp_ratio)
        status_bonus = 1.5 if getattr(encounter, "status_effect", None) else 1.0
        return min(0.95, max(0.03, species["catch_rate"] / 255 * hp_factor * BALLS[ball_sku] * status_bonus))

    async def attack(self, channel_id: int, damage: int, encounter_id: int | None = None):
        encounter = (await self.repo.get_active(channel_id, encounter_id, lock=True)
                     if encounter_id is not None else await self.repo.active_in_channel(channel_id, lock=True))
        if not encounter:
            raise ValueError("That encounter has ended." if encounter_id is not None else "There is no active encounter in this channel.")
        if json.loads(getattr(encounter, "battle_state_json", "{}") or "{}"):
            raise ValueError("Use the battle's move buttons to attack.")
        encounter.current_hp = max(1, encounter.current_hp - max(1, min(damage, 50)))
        await self.session.flush()
        return encounter

    async def attempt_catch(self, channel_id: int, discord_id: int, ball_sku: str, user_repo, inventory_repo,
                            encounter_id: int | None = None, battle_turn: bool = False, battle_state=None):
        encounter = (await self.repo.get_active(channel_id, encounter_id, lock=True)
                     if encounter_id is not None else await self.repo.active_in_channel(channel_id, lock=True))
        if not encounter:
            raise ValueError("That encounter has ended." if encounter_id is not None else "There is no active encounter in this channel.")
        battle = battle_state
        if battle_turn:
            if not battle or battle.get("owner") != discord_id or battle.get("finished"):
                raise ValueError("Use the ball buttons in your wild battle.")
        elif json.loads(getattr(encounter, "battle_state_json", "{}") or "{}"):
            raise ValueError("Use the ball buttons in your wild battle.")
        user = await user_repo.get_by_discord_id_locked(discord_id)
        if not user:
            raise ValueError("Use /start before catching Pokémon.")
        item = await inventory_repo.get_item_locked(discord_id, ball_sku)
        if not item or item.quantity < 1:
            raise ValueError(f"You do not have a {ball_sku}.")
        item.quantity -= 1
        battle_hp = battle["wild"]["hp"] if battle_turn and battle else None
        caught = self.rng.random() <= self.catch_probability(encounter, ball_sku, battle_hp)
        if not caught:
            await self.session.flush()
            return None
        data = self.registry.species(encounter.species)
        types = data["types"]
        traits = PokemonTraitsService(self.rng).roll(types, data)
        mon = PokemonInstance(
            owner_id=user.id, species=encounter.species, dex_number=data["dex_number"], level=encounter.level,
            current_hp=battle_hp if battle_hp is not None else encounter.current_hp, max_hp=encounter.max_hp,
            attack=data["base_attack"] + encounter.level, defense=data["base_defense"] + encounter.level,
            speed=data["base_speed"] + encounter.level, primary_type=types[0],
            secondary_type=types[1] if len(types) > 1 else None,
            shiny=self.rng.randint(1, 4096) == 1,
            iv_hp=self.rng.randint(0, 31), iv_attack=self.rng.randint(0, 31),
            iv_defense=self.rng.randint(0, 31), iv_speed=self.rng.randint(0, 31),
            nature=traits["nature"], ability=traits["ability"], gender=traits["gender"],
        )
        MovesetV80Service().initialize(mon, self.registry)
        self.session.add(mon)
        if not battle_turn:
            encounter.status = "caught"
            encounter.claimed_by_discord_id = discord_id
        user.balance += CATCH_GOLD_REWARD
        from services.daily_mission_service import DailyMissionService
        await DailyMissionService(self.session).record(discord_id, 'catch')
        await PokedexRepository(self.session).record(discord_id, encounter.species, caught=True)
        TrainerProgressionService().grant(user, 25 + encounter.level)
        await self.session.flush()
        return mon

