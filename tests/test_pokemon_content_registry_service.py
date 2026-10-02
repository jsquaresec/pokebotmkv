from services.pokemon_content_registry_service import PokemonContentRegistryService

def run():
    svc = PokemonContentRegistryService()
    species = svc.all_species()
    assert len(species) >= 151
    assert "Pikachu" in species
    assert svc.total_forms() > 0
    print("pokemon content registry service tests passed")

if __name__ == "__main__":
    run()
