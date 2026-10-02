import json
from pathlib import Path

class SpeciesService:
    def __init__(self, species_path: str = "data/species.json"):
        self.species_data = json.loads(Path(species_path).read_text(encoding="utf-8"))

    def list_species(self) -> list[dict]:
        return self.species_data

    def get_species(self, name: str) -> dict | None:
        for row in self.species_data:
            if row["name"] == name:
                return row
        return None

    def rarity_of(self, name: str) -> str:
        row = self.get_species(name)
        return row.get("rarity", "common") if row else "common"
