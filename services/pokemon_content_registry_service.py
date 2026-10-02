import json
from pathlib import Path

class PokemonContentRegistryService:
    def __init__(
        self,
        species_path: str = "data/pokemon_species_kanto.json",
        forms_path: str = "data/pokemon_forms_registry.json",
        variants_path: str = "data/pokemon_variants.json",
    ):
        self.species = json.loads(Path(species_path).read_text(encoding="utf-8"))
        self.forms = json.loads(Path(forms_path).read_text(encoding="utf-8"))
        self.variants = json.loads(Path(variants_path).read_text(encoding="utf-8"))

    def all_species(self) -> list[str]:
        return list(self.species)

    def forms_for(self, species: str) -> list[str]:
        return list(self.forms.get(species, []))

    def has_variant(self, variant_code: str) -> bool:
        return bool(self.variants.get(variant_code, False))

    def total_forms(self) -> int:
        return sum(len(v) for v in self.forms.values())
