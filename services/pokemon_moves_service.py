import json
from pathlib import Path
from services.content_registry_v70 import ContentRegistryV70

class PokemonMovesService:
    def __init__(self, path: str = "data/level_up_moves.json"):
        self.level_moves = json.loads(Path(path).read_text(encoding="utf-8"))
        self.registry = ContentRegistryV70()

    def moves_for_species_level(self, species: str, level: int) -> list[str]:
        levels = self.level_moves.get(species, {})
        learned = []
        for lvl_str, moves in levels.items():
            if int(lvl_str) <= level:
                for move in moves:
                    if move not in learned:
                        learned.append(move)
        supported = [name for name in learned if (self.registry.move(name) or {}).get('battle_supported', False)]
        return supported or ["Struggle"]

    def is_legal_move(self, species: str, level: int, move_name: str) -> bool:
        return move_name in self.moves_for_species_level(species, level)
