class BattleEmbedService:
    def render_summary_text(self, battle_id: int, state: dict) -> str:
        p1 = state["player_one"]
        p2 = state["player_two"]
        p1_bench = ", ".join(f'{m["name"]} {m["hp"]}/{m["max_hp"]}' for m in p1["bench"]) or "none"
        p2_bench = ", ".join(f'{m["name"]} {m["hp"]}/{m["max_hp"]}' for m in p2["bench"]) or "none"
        lines = [
            f"Battle #{battle_id} | Turn {state['turn']}",
            f"P1 Active: {p1['active']['name']} {p1['active']['hp']}/{p1['active']['max_hp']} | Status: {p1['active']['status']}",
            f"P1 Bench: {p1_bench}",
            f"P2 Active: {p2['active']['name']} {p2['active']['hp']}/{p2['active']['max_hp']} | Status: {p2['active']['status']}",
            f"P2 Bench: {p2_bench}",
        ]
        return "\n".join(lines)

    def render_log_tail(self, state: dict, lines: int = 8) -> str:
        tail = state["log"][-lines:] if len(state["log"]) >= lines else state["log"]
        return "\n".join(tail) if tail else "No battle events yet."
