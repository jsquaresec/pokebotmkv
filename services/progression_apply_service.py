from services.progression_service import ProgressionService
from services.pokemon_moves_service import PokemonMovesService

class ProgressionApplyService:
    def __init__(self):
        self.progression = ProgressionService()
        self.moves = PokemonMovesService()

    def apply_battle_xp_to_party_member(self, pokemon, xp: int) -> dict:
        old_level = pokemon.level
        new_level, leveled = self.progression.apply_xp(pokemon, xp)
        unlocked = []
        if leveled:
            before = self.moves.moves_for_species_level(pokemon.species, old_level)
            after = self.moves.moves_for_species_level(pokemon.species, new_level)
            unlocked = [m for m in after if m not in before]
        return {
            "old_level": old_level,
            "new_level": new_level,
            "leveled": leveled,
            "unlocked_moves": unlocked,
        }
