class DailyMissionChainService:
    def __init__(self):
        self.progress = {}

    def missions(self):
        return [
            {"code": "catch_1", "target": 1},
            {"code": "battle_1", "target": 1},
            {"code": "shop_visit", "target": 1},
        ]

    def advance(self, user_id: int, code: str, amount: int = 1):
        user = self.progress.setdefault(user_id, {})
        user[code] = user.get(code, 0) + amount
        return user[code]

    def summary(self, user_id: int):
        user = self.progress.get(user_id, {})
        out = []
        for mission in self.missions():
            out.append({
                "code": mission["code"],
                "progress": min(user.get(mission["code"], 0), mission["target"]),
                "target": mission["target"],
                "complete": user.get(mission["code"], 0) >= mission["target"],
            })
        return out
