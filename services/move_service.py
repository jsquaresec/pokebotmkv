from battle.move_engine import MoveEngine

class MoveService:
    def __init__(self):
        self.engine = MoveEngine()

    def default_move_for(self, mon_name: str) -> str:
        return self.engine.choose_default_move(mon_name)

    def validate_move_choice(self, move_name: str) -> str:
        move = self.engine.get_move(move_name)
        if move is None:
            raise ValueError(f"Unknown move: {move_name}")
        return move["name"]
