from services.rarity_service import RarityService
from services.embed_factory import EmbedFactory

class SpawnWorker:
    def __init__(self):
        self.rarity = RarityService()
        self.embed_factory = EmbedFactory()
        self.species_pool = {
            "common": ["Pidgey", "Rattata", "Caterpie"],
            "uncommon": ["Oddish", "Eevee"],
            "rare": ["Pikachu", "Bulbasaur"],
            "epic": ["Charmander", "Squirtle"],
            "legendary": ["Mew"],
        }

    def generate_spawn_message(self) -> str:
        rarity = self.rarity.roll_rarity()
        species = self.species_pool.get(rarity, ["Pidgey"])[0]
        return self.embed_factory.spawn_card(species, rarity, 5)

if __name__ == "__main__":
    print(SpawnWorker().generate_spawn_message())
