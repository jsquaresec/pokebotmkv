class EventEffectService:
    def __init__(self):
        self.flags = {
            "double_xp_weekend": False,
            "rare_spawn_hour": False,
            "legendary_event": False,
        }

    def status(self) -> dict:
        return dict(self.flags)

    def set_flag(self, code: str, enabled: bool) -> dict:
        if code not in self.flags:
            raise ValueError("Unknown event code.")
        self.flags[code] = enabled
        return self.status()

    def xp_multiplier(self) -> int:
        return 2 if self.flags.get("double_xp_weekend") else 1

    def spawn_bias(self) -> str | None:
        if self.flags.get("legendary_event"):
            return "rare"
        if self.flags.get("rare_spawn_hour"):
            return "uncommon"
        return None
