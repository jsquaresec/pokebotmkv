from services.pokemon_variation_service import PokemonVariationService

def run():
    svc = PokemonVariationService()
    name = svc.build_display_name("Pikachu", form="Gigantamax", shiny=True, radiant=True)
    assert "Pikachu" in name
    assert "Shiny" in name
    assert "Radiant" in name
    print("pokemon variation service tests passed")

if __name__ == "__main__":
    run()
