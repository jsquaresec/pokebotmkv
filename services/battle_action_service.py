class BattleActionService:
    def submit_move(self, state: dict, actor_discord_id: int, move_name: str) -> dict:
        if state["finished"]:
            raise ValueError("Battle already finished.")
        p1_id = state["player_one"]["discord_id"]
        p2_id = state["player_two"]["discord_id"]
        action = {"type": "move", "move_name": move_name}

        if actor_discord_id == p1_id:
            if state["pending_action_p1"] is not None:
                raise ValueError("Player one already submitted an action this turn.")
            state["pending_action_p1"] = action
        elif actor_discord_id == p2_id:
            if state["pending_action_p2"] is not None:
                raise ValueError("Player two already submitted an action this turn.")
            state["pending_action_p2"] = action
        else:
            raise ValueError("You are not part of this battle.")
        return state

    def submit_switch(self, state: dict, actor_discord_id: int, target_slot: int) -> dict:
        if state["finished"]:
            raise ValueError("Battle already finished.")
        p1_id = state["player_one"]["discord_id"]
        p2_id = state["player_two"]["discord_id"]
        action = {"type": "switch", "target_slot": target_slot}

        if actor_discord_id == p1_id:
            if state["pending_action_p1"] is not None:
                raise ValueError("Player one already submitted an action this turn.")
            state["pending_action_p1"] = action
        elif actor_discord_id == p2_id:
            if state["pending_action_p2"] is not None:
                raise ValueError("Player two already submitted an action this turn.")
            state["pending_action_p2"] = action
        else:
            raise ValueError("You are not part of this battle.")
        return state

    def both_ready(self, state: dict) -> bool:
        return state["pending_action_p1"] is not None and state["pending_action_p2"] is not None
