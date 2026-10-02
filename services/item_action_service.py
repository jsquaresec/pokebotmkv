from services.content_registry_v70 import ContentRegistryV70
from services.moveset_v80_service import MovesetV80Service
from services.progression_v70_service import ProgressionV70Service


class ItemActionService:
    HEALING = {"potion": 20, "super_potion": 60, "max_potion": 99999}

    def __init__(self, session, inventory_repo, pokemon_repo):
        self.session = session
        self.inventory = inventory_repo
        self.pokemon = pokemon_repo

    async def use(self, discord_id: int, owner_id: int, pokemon_id: int, sku: str):
        item = await self.inventory.get_item_locked(discord_id, sku)
        mon = await self.pokemon.get_by_id_locked(pokemon_id)
        if not item or item.quantity < 1:
            raise ValueError(f"You do not have a {sku}.")
        if not mon or mon.owner_id != owner_id or mon.locked:
            raise ValueError("That Pokémon is unavailable.")
        if sku in self.HEALING:
            if mon.current_hp >= mon.max_hp:
                raise ValueError("That Pokémon already has full HP.")
            before = mon.current_hp
            mon.current_hp = min(mon.max_hp, mon.current_hp + self.HEALING[sku])
            result = f"restored {mon.current_hp - before} HP"
        elif sku == "rare_candy":
            if mon.level >= 100:
                raise ValueError("That Pokémon is already at the level cap.")
            registry = ContentRegistryV70()
            needed = max(0, (mon.level + 1) ** 3 - mon.experience)
            outcome = ProgressionV70Service().grant_experience(mon, needed, registry)
            result = f"reached level {mon.level}"
            if outcome["can_evolve_to"]:
                result += f" and can evolve into {outcome['can_evolve_to']}"
        elif sku == "ether":
            slots = MovesetV80Service.load(mon)
            if not slots or all(slot["pp"] >= slot["max_pp"] for slot in slots):
                raise ValueError("No move PP needs restoring.")
            MovesetV80Service().restore_pp(mon)
            result = "restored all move PP"
        else:
            raise ValueError("That item cannot be used directly.")
        item.quantity -= 1
        await self.session.flush()
        return mon, result

    async def equip(self, discord_id: int, owner_id: int, pokemon_id: int, sku: str):
        item = await self.inventory.get_item_locked(discord_id, sku)
        mon = await self.pokemon.get_by_id_locked(pokemon_id)
        if not item or item.quantity < 1 or not mon or mon.owner_id != owner_id or mon.locked:
            raise ValueError("Item or Pokémon is unavailable.")
        if mon.held_item:
            await self.inventory.add_item(discord_id, mon.held_item, 1)
        item.quantity -= 1
        mon.held_item = sku
        await self.session.flush()
        return mon
