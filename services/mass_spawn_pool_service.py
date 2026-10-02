import random
from services.pokemon_content_registry_service import PokemonContentRegistryService
from services.featured_rotation_service import FeaturedRotationService

class MassSpawnPoolService:
    def __init__(self):
        self.registry = PokemonContentRegistryService()
        self.rotations = FeaturedRotationService()

    def random_species(self, include_featured_bias: bool = True, week_number: int | None = None) -> str:
        species = self.registry.all_species()
        if include_featured_bias:
            featured = self.rotations.current_pool(week_number)
            weighted = species + featured + featured
            return random.choice(weighted)
        return random.choice(species)
