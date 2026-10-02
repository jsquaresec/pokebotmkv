class LiveEventToggleService:
    def __init__(self):
        self.flags = {
            "double_xp_weekend": False,
            "rare_spawn_hour": False,
            "legendary_event": False,
        }

    def status(self) -> dict:
        return dict(self.flags)

    def enable(self, code: str) -> dict:
        if code not in self.flags:
            raise ValueError("Unknown event code.")
        self.flags[code] = True
        return self.status()

    def disable(self, code: str) -> dict:
        if code not in self.flags:
            raise ValueError("Unknown event code.")
        self.flags[code] = False
        return self.status()
