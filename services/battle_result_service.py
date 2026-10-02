class BattleResultService:
    def render_result(self, battle_id: int, winner_name: str | None, coins: int, xp: int, leveled_msg: str = "") -> str:
        base = f"Battle #{battle_id} complete. Winner: {winner_name or 'Unknown'}. Rewards: {coins} coins, {xp} XP."
        if leveled_msg:
            base += " " + leveled_msg
        return base
