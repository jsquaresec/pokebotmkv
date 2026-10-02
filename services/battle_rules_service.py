from services.pokemon_moves_service import PokemonMovesService

class BattleRulesService:
    def __init__(self):
        self.moves = PokemonMovesService()

    def validate_move_choice(self, active_species: str, active_level: int | str, move_name: str | None = None) -> str:
        if move_name is None:
            move_name = str(active_level)
            active_level = 100
        if not self.moves.is_legal_move(active_species, active_level, move_name):
            raise ValueError(f"{active_species} cannot use {move_name} at level {active_level}.")
        return move_name

    def validate_switch_target(self, player_state: dict, target_slot: int) -> int:
        if target_slot < 2:
            raise ValueError("You can only switch to bench slots 2-6.")
        bench_index = target_slot - 2
        if bench_index >= len(player_state["bench"]):
            raise ValueError("That bench slot does not exist.")
        mon = player_state["bench"][bench_index]
        if mon["hp"] <= 0:
            raise ValueError("Cannot switch to a fainted Pokémon.")
        return bench_index
