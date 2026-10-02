from battle.move_engine import MoveEngine

class TurnEngine:
    def __init__(self):
        self.move_engine = MoveEngine()

    def _priority_value(self, move_name: str) -> int:
        move = self.move_engine.get_move(move_name)
        if not move:
            return 0
        return move.get('priority', 1 if move.get("effect") == "priority" else 0)

    def _first_available_bench_index(self, player_state: dict):
        for idx, mon in enumerate(player_state["bench"]):
            if mon["hp"] > 0:
                return idx
        return None

    def _apply_switch(self, player_state: dict, target_slot: int, state: dict, actor_name: str):
        bench_index = target_slot - 2
        if bench_index < 0 or bench_index >= len(player_state["bench"]):
            raise ValueError("Invalid switch target.")
        target = player_state["bench"][bench_index]
        if target["hp"] <= 0:
            raise ValueError("Cannot switch to a fainted Pokémon.")
        old_active = player_state["active"]
        player_state["bench"][bench_index] = old_active
        player_state["active"] = target
        player_state["active_slot"] = target_slot - 1
        state["log"].append(f'{actor_name} switched to {target["name"]}!')

    def _process_status_end_turn(self, side: dict, label: str, state: dict):
        active = side["active"]
        status = active.get("status")
        if status == "burned":
            dmg = max(1, active["max_hp"] // 16)
            active["hp"] = max(0, active["hp"] - dmg)
            state["log"].append(f'{label} {active["name"]} is hurt by its burn ({dmg}).')
        elif status == "poisoned":
            dmg = max(1, active["max_hp"] // 8)
            active["hp"] = max(0, active["hp"] - dmg)
            state["log"].append(f'{label} {active["name"]} is hurt by poison ({dmg}).')

    def first_actor(self, state: dict) -> str:
        p1 = state["player_one"]["active"]
        p2 = state["player_two"]["active"]
        p1_move = (state.get("pending_action_p1") or {}).get("move_name", "Tackle")
        p2_move = (state.get("pending_action_p2") or {}).get("move_name", "Tackle")
        p1_pri = self._priority_value(p1_move)
        p2_pri = self._priority_value(p2_move)
        if p1_pri != p2_pri:
            return "player_one" if p1_pri > p2_pri else "player_two"
        return "player_one" if p1["speed"] >= p2["speed"] else "player_two"

    def _resolve_action(self, state: dict, attacker_key: str, defender_key: str, action: dict | None):
        attacker_side = state[attacker_key]
        defender_side = state[defender_key]
        attacker = attacker_side["active"]
        defender = defender_side["active"]

        if defender["hp"] <= 0 or attacker["hp"] <= 0:
            return
        if action is None:
            action = {"type": "move", "move_name": "Tackle"}

        if action["type"] == "switch":
            self._apply_switch(attacker_side, action["target_slot"], state, attacker_key.replace("_", " ").title())
            return

        move_name = action.get("move_name", "Tackle")
        self.move_engine.resolve_move(attacker, defender, move_name, state)

        if defender["hp"] == 0:
            next_idx = self._first_available_bench_index(defender_side)
            if next_idx is not None:
                defender_side["requires_replacement"] = True
                state["log"].append(f'{defender_key.replace("_", " ").title()} must choose a replacement.')
            else:
                state["finished"] = True
                state["winner_discord_id"] = attacker["discord_id"]

    def _auto_replace_if_possible(self, side: dict, label: str, state: dict):
        if not side.get("requires_replacement"):
            return
        next_idx = self._first_available_bench_index(side)
        if next_idx is None:
            return
        replacement = side["bench"][next_idx]
        old_active = side["active"]
        side["bench"][next_idx] = old_active
        side["active"] = replacement
        side["active_slot"] = next_idx + 1
        side["requires_replacement"] = False
        state["log"].append(f'{label} sent out {replacement["name"]}!')

    def resolve_turn(self, state: dict) -> dict:
        if state["finished"]:
            raise ValueError("Battle already finished.")
        for side in ('player_one', 'player_two'):
            for mon in [state[side]['active'], *state[side]['bench']]:
                mon.pop('flinch', None)
                mon['physical_damage_taken'] = 0
                mon['special_damage_taken'] = 0

        first_key = self.first_actor(state)
        second_key = "player_two" if first_key == "player_one" else "player_one"

        action_first = state["pending_action_p1"] if first_key == "player_one" else state["pending_action_p2"]
        action_second = state["pending_action_p2"] if first_key == "player_one" else state["pending_action_p1"]

        second_original = state[second_key]["active"]
        self._resolve_action(state, first_key, second_key, action_first)
        if not state["finished"]:
            self._auto_replace_if_possible(state["player_one"], "Player One", state)
            self._auto_replace_if_possible(state["player_two"], "Player Two", state)

        if not state["finished"] and second_original["hp"] > 0:
            self._resolve_action(state, second_key, first_key, action_second)
        if not state["finished"]:
            self._auto_replace_if_possible(state["player_one"], "Player One", state)
            self._auto_replace_if_possible(state["player_two"], "Player Two", state)

        if not state["finished"]:
            self._process_status_end_turn(state["player_one"], "Player One", state)
            self._process_status_end_turn(state["player_two"], "Player Two", state)

        if state["player_one"]["active"]["hp"] <= 0 and not any(m["hp"] > 0 for m in state["player_one"]["bench"]):
            state["finished"] = True
            state["winner_discord_id"] = state["player_two"]["discord_id"]
        if state["player_two"]["active"]["hp"] <= 0 and not any(m["hp"] > 0 for m in state["player_two"]["bench"]):
            state["finished"] = True
            state["winner_discord_id"] = state["player_one"]["discord_id"]

        state["pending_action_p1"] = None
        state["pending_action_p2"] = None
        if not state["finished"]:
            state["turn"] += 1
        return state
