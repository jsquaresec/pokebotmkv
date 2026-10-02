import json
from datetime import datetime
from pathlib import Path

class FeaturedRotationService:
    def __init__(self, path: str = "data/featured_rotations.json"):
        self.rotations = json.loads(Path(path).read_text(encoding="utf-8"))
        self.order = list(self.rotations.keys())

    def current_rotation_key(self, week_number: int | None = None) -> str:
        if not self.order:
            raise ValueError("No rotations configured.")
        if week_number is None:
            week_number = datetime.utcnow().isocalendar().week
        return self.order[(week_number - 1) % len(self.order)]

    def current_pool(self, week_number: int | None = None) -> list[str]:
        key = self.current_rotation_key(week_number)
        return list(self.rotations[key])
