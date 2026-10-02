import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=64)
def _read(path, modified):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ContentRegistryV70:
    REGIONS = ("kanto", "johto", "hoenn", "sinnoh", "unova", "kalos", "alola", "galar", "hisui", "paldea")

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._stats = {row["name"].casefold(): row for row in self._load("species.json")}
        self._moves = {row["name"].casefold(): row for row in self._load("moves.json")}
        self._learnsets = self._load("species_moves.json")
        self._names = []
        for region in self.REGIONS:
            self._names.extend(self._load(f"pokemon_species_{region}.json"))
        self._names = list(dict.fromkeys(self._names))
        self._canonical = {name.casefold(): name for name in self._names}

    def _load(self, name):
        path = (self.data_dir / name).resolve()
        return _read(str(path), path.stat().st_mtime_ns)

    def all_species(self):
        return list(self._names)

    def species(self, name: str) -> dict | None:
        canonical = self._canonical.get(name.casefold())
        if canonical is None:
            return None
        if canonical.casefold() not in self._stats:
            raise ValueError(f"Missing catalog data for {canonical}.")
        return dict(self._stats[canonical.casefold()])

    def move(self, name: str):
        return self._moves.get(name.casefold())

    def legal_moves(self, species: str, level: int, *, supported_only=True):
        canonical = self._canonical.get(species.casefold(), species)
        rows = self._learnsets.get(canonical, [])
        names = [row if isinstance(row, str) else row["move"] for row in rows if isinstance(row, str) or row.get("level", 1) <= level]
        return list(dict.fromkeys(name for name in names if not supported_only or
            (self.move(name) and self.move(name).get("battle_supported", True))))

    def validate(self):
        errors = []
        for name in self._names:
            data = self._stats.get(name.casefold())
            if not data:
                errors.append(f"{name}: missing species data")
                continue
            for key in ("dex_number", "base_hp", "base_attack", "base_defense", "base_speed",
                        "base_special_attack", "base_special_defense", "types", "abilities", "growth_rate"):
                if not data.get(key):
                    errors.append(f"{name}: missing {key}")
            if not self._learnsets.get(name):
                errors.append(f"{name}: missing learnset")
        for species, learnset in self._learnsets.items():
            for row in learnset:
                name = row if isinstance(row, str) else row["move"]
                if name.casefold() not in self._moves:
                    errors.append(f"{species}: unknown move {name}")
        return errors
