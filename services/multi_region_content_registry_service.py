import json
from pathlib import Path

class MultiRegionContentRegistryService:
    REGION_FILES = {
        "kanto": "data/pokemon_species_kanto.json",
        "johto": "data/pokemon_species_johto.json",
        "hoenn": "data/pokemon_species_hoenn.json",
        "sinnoh": "data/pokemon_species_sinnoh.json",
        "unova": "data/pokemon_species_unova.json",
        "kalos": "data/pokemon_species_kalos.json",
        "alola": "data/pokemon_species_alola.json",
        "galar": "data/pokemon_species_galar.json",
        "hisui": "data/pokemon_species_hisui.json",
        "paldea": "data/pokemon_species_paldea.json",
    }

    def __init__(self):
        self.regions = {}
        for key, file_path in self.REGION_FILES.items():
            self.regions[key] = json.loads(Path(file_path).read_text(encoding="utf-8"))

    def region_names(self) -> list[str]:
        return list(self.regions.keys())

    def region_pool(self, region: str) -> list[str]:
        return list(self.regions.get(region.lower(), []))

    def all_species(self) -> list[str]:
        merged = []
        seen = set()
        for region in self.region_names():
            for species in self.regions[region]:
                if species not in seen:
                    seen.add(species)
                    merged.append(species)
        return merged

    def counts(self) -> dict:
        return {region: len(pool) for region, pool in self.regions.items()}
