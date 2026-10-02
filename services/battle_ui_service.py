class BattleUIService:
    def hp_bar(self, hp: int, max_hp: int, width: int = 10) -> str:
        if max_hp <= 0:
            return "[" + "-" * width + "]"
        filled = max(0, min(width, round((hp / max_hp) * width)))
        return "[" + "█" * filled + "░" * (width - filled) + "]"

    def render_battle_view(self, battle_id: int, state: dict, timer_seconds: int = 0) -> str:
        p1 = state["player_one"]["active"]
        p2 = state["player_two"]["active"]
        return (
            f"Battle #{battle_id} | Turn {state['turn']} | Timer {timer_seconds}s\n"
            f"P1 {p1['name']} Lv.{p1.get('level', 1)} {self.hp_bar(p1['hp'], p1['max_hp'])} {p1['hp']}/{p1['max_hp']}\n"
            f"P2 {p2['name']} Lv.{p2.get('level', 1)} {self.hp_bar(p2['hp'], p2['max_hp'])} {p2['hp']}/{p2['max_hp']}"
        )
