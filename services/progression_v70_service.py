class ProgressionV70Service:
    @staticmethod
    def experience_for_level(level: int) -> int:
        return max(0, level ** 3)

    def grant_experience(self, pokemon, amount: int, registry):
        if amount < 0:
            raise ValueError("Experience cannot be negative.")
        pokemon.experience += amount
        old_level = pokemon.level
        while pokemon.level < 100 and pokemon.experience >= self.experience_for_level(pokemon.level + 1):
            pokemon.level += 1
            pokemon.max_hp += 2
            pokemon.current_hp += 2
            pokemon.attack += 1
            pokemon.defense += 1
            pokemon.speed += 1
        data = registry.species(pokemon.species) or {}
        evolved = None
        if data.get("evolves_to") and pokemon.level >= data.get("evolution_level", 101):
            evolved = data["evolves_to"]
        return {"levels_gained": pokemon.level - old_level, "can_evolve_to": evolved}

    def evolve(self, pokemon, registry):
        data = registry.species(pokemon.species) or {}
        target = data.get("evolves_to")
        if not target or pokemon.level < data.get("evolution_level", 101):
            raise ValueError("This Pokémon does not currently meet its evolution requirements.")
        pokemon.species = target
        target_data = registry.species(target)
        if target_data:
            pokemon.dex_number = target_data["dex_number"]
            pokemon.primary_type = target_data["types"][0]
            pokemon.secondary_type = target_data["types"][1] if len(target_data["types"]) > 1 else None
            from services.catalog_upgrade_service import CatalogUpgradeService
            pokemon.catalog_revision = 0
            CatalogUpgradeService(registry).upgrade(pokemon)
        return pokemon
