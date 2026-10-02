import random
from services.species_service import SpeciesService
from services.pokemon_service import PokemonService

class CatchService:
    def __init__(self, species_service: SpeciesService, pokemon_service: PokemonService):
        self.species_service = species_service
        self.pokemon_service = pokemon_service

    def spawn_random(self) -> dict:
        return random.choice(self.species_service.list_species())

    async def catch_spawn(self, owner_id: int, spawn: dict):
        return await self.pokemon_service.create_pokemon(owner_id=owner_id, species=spawn["name"], level=spawn.get("level", 5))
