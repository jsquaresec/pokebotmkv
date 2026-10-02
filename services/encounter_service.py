import json
import random
from pathlib import Path

class EncounterService:
    def __init__(self, path: str = "data/encounter_table.json"):
        self.table = json.loads(Path(path).read_text(encoding="utf-8"))

    def roll_rarity(self) -> str:
        roll = random.randint(1, 100)
        if roll <= 70:
            return "common"
        if roll <= 93:
            return "uncommon"
        return "rare"

    def random_species(self) -> str:
        rarity = self.roll_rarity()
        pool = self.table.get(rarity, []) or self.table.get("common", [])
        return random.choice(pool)
