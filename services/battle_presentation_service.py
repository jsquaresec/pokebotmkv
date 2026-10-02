class BattlePresentationService:
    def hp_bar(self, hp: int, max_hp: int, width: int = 16) -> str:
        if max_hp <= 0:
            return "[" + "░" * width + "]"
        filled = max(0, min(width, round((hp / max_hp) * width)))
        return "[" + "█" * filled + "░" * (width - filled) + "]"

    def render_battle_card(self, p1: dict, p2: dict, turn: int, timer_seconds: int) -> str:
        return (
            f"⚔️ Battle View | Turn {turn} | Timer {timer_seconds}s\n\n"
            f"{p1['name']} Lv.{p1.get('level', 1)}\n"
            f"{self.hp_bar(p1['hp'], p1['max_hp'])} {p1['hp']}/{p1['max_hp']}\n\n"
            f"{p2['name']} Lv.{p2.get('level', 1)}\n"
            f"{self.hp_bar(p2['hp'], p2['max_hp'])} {p2['hp']}/{p2['max_hp']}"
        )

    def render_result_card(self, winner: str, coins: int, xp: int, extras: str = "") -> str:
        text = f"🏆 Winner: {winner}\n💰 Coins: {coins}\n⭐ XP: {xp}"
        if extras:
            text += f"\n{extras}"
        return text
