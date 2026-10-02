import random
from models.pokemon import PokemonInstance
from repositories.pokemon import PokemonRepository
from services.species_service import SpeciesService
from services.pokemon_traits_service import PokemonTraitsService
from services.content_registry_v70 import ContentRegistryV70
from services.moveset_v80_service import MovesetV80Service

class PokemonService:
    def __init__(self, repo: PokemonRepository, species_service: SpeciesService):
        self.repo = repo
        self.species_service = species_service

    async def create_pokemon(self, owner_id: int, species: str, level: int = 5) -> PokemonInstance:
        data = self.species_service.get_species(species)
        if not data:
            raise ValueError("Unknown Pokémon species.")
        hp = data.get("base_hp", 20) + level * 2
        attack = data.get("base_attack", 10) + level
        defense = data.get("base_defense", 10) + level
        speed = data.get("base_speed", 10) + level
        types = data.get("types", ["normal"])
        traits = PokemonTraitsService(random).roll(types, data)
        pokemon = PokemonInstance(
            owner_id=owner_id,
            species=species,
            dex_number=data['dex_number'],
            level=level,
            current_hp=hp,
            max_hp=hp,
            attack=attack,
            defense=defense,
            speed=speed,
            shiny=(random.randint(1, 4096) == 1),
            primary_type=types[0], secondary_type=types[1] if len(types) > 1 else None,
            nature=traits["nature"], ability=traits["ability"], gender=traits["gender"],
        )
        MovesetV80Service().initialize(pokemon, ContentRegistryV70())
        return await self.repo.add(pokemon)
