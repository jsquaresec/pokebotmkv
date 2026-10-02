class BattleUIPolishService:
    def hp_bar(self, hp: int, max_hp: int, width: int = 12) -> str:
        if max_hp <= 0:
            return "[" + "-" * width + "]"
        filled = max(0, min(width, round((hp / max_hp) * width)))
        return "[" + "█" * filled + "░" * (width - filled) + "]"

    def render_turn_state(self, p1_name: str, p1_hp: int, p1_max: int, p2_name: str, p2_hp: int, p2_max: int, turn: int) -> str:
        return (
            f"Turn {turn}\n"
            f"{p1_name}: {self.hp_bar(p1_hp, p1_max)} {p1_hp}/{p1_max}\n"
            f"{p2_name}: {self.hp_bar(p2_hp, p2_max)} {p2_hp}/{p2_max}"
        )
