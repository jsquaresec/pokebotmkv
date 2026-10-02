import json


class MovesetV80Service:
    MAX_MOVES = 4

    @staticmethod
    def load(pokemon):
        try:
            return json.loads(pokemon.moves_json or "[]")
        except (TypeError, json.JSONDecodeError):
            return []

    def initialize(self, pokemon, registry):
        names = registry.legal_moves(pokemon.species, pokemon.level)[-self.MAX_MOVES :]
        pokemon.moves_json = json.dumps([self._slot(name, registry) for name in names])
        return self.load(pokemon)

    def learn(self, pokemon, move_name: str, registry, replace_index: int | None = None):
        legal = registry.legal_moves(pokemon.species, pokemon.level)
        if move_name not in legal:
            raise ValueError(f"{pokemon.species} cannot learn {move_name} at level {pokemon.level}.")
        slots = self.load(pokemon)
        if any(x["name"].casefold() == move_name.casefold() for x in slots):
            raise ValueError("That move is already learned.")
        slot = self._slot(move_name, registry)
        if len(slots) < self.MAX_MOVES:
            slots.append(slot)
        elif replace_index is not None and 1 <= replace_index <= self.MAX_MOVES:
            slots[replace_index - 1] = slot
        else:
            raise ValueError("Moveset is full; provide a slot from 1 to 4 to replace.")
        pokemon.moves_json = json.dumps(slots)
        return slots

    @staticmethod
    def _slot(name, registry):
        move = registry.move(name)
        if move is None:
            raise ValueError(f"Unknown move: {name}")
        return {"name": name, "pp": move.get("pp", 35), "max_pp": move.get("pp", 35)}

    def restore_pp(self, pokemon):
        slots = self.load(pokemon)
        for slot in slots:
            slot["pp"] = slot["max_pp"]
        pokemon.moves_json = json.dumps(slots)
        return slots
