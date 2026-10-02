from services.pokemon_moves_service import PokemonMovesService

def run():
    svc = PokemonMovesService("data/level_up_moves.json")
    moves = svc.moves_for_species_level("Pikachu", 8)
    assert "Thunder Shock" in moves
    assert "Quick Attack" in moves
    assert svc.is_legal_move("Bulbasaur", 8, "Vine Whip") is True
    assert svc.is_legal_move("Bulbasaur", 2, "Vine Whip") is False
    assert svc.is_legal_move("Bulbasaur", 3, "Vine Whip") is True
    print("pokemon moves service tests passed")

if __name__ == "__main__":
    run()
