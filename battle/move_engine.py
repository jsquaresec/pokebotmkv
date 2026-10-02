import json
import random
from pathlib import Path

class MoveEngine:
    def __init__(self, moves_path: str = "data/moves.json"):
        self.moves = json.loads(Path(moves_path).read_text(encoding="utf-8"))

    def get_move(self, name: str) -> dict | None:
        for move in self.moves:
            if move["name"].lower() == name.lower():
                return move
        return None

    def choose_default_move(self, mon_name: str) -> str:
        name = mon_name.lower()
        if "pikachu" in name:
            return "Thunder Shock"
        if "bulbasaur" in name:
            return "Vine Whip"
        return "Tackle"

    def calc_damage(self, attacker: dict, defender: dict, move: dict) -> int:
        if move["category"] == "status" or move["power"] <= 0:
            return 0
        attack_stage = attacker.get("stat_stages", {}).get("attack", 0)
        defense_stage = defender.get("stat_stages", {}).get("defense", 0)
        def stage(n):
            return (2 + n) / 2 if n >= 0 else 2 / (2 - n)
        base_attack = attacker["attack"] * stage(attack_stage)
        base_defense = max(1, defender["defense"] * stage(defense_stage))
        level = attacker.get("level", 5)
        base = (((2 * level / 5 + 2) * move["power"] * base_attack / base_defense) / 50) + 2
        move_type = move.get("type", "normal")
        stab = 1.5 if move_type in attacker.get("types", []) else 1.0
        effectiveness = self.type_multiplier(move_type, defender.get("types", ["normal"]))
        critical = 1.5 if random.random() < 1 / 24 else 1.0
        variance = random.uniform(0.85, 1.0)
        return max(1, int(base * stab * effectiveness * critical * variance)) if effectiveness else 0

    @staticmethod
    def type_multiplier(move_type: str, defender_types: list[str]) -> float:
        chart = {
            "normal": {"ghost": 0}, "fire": {"grass": 2, "bug": 2, "water": .5, "fire": .5, "rock": .5},
            "water": {"fire": 2, "rock": 2, "ground": 2, "water": .5, "grass": .5},
            "grass": {"water": 2, "ground": 2, "rock": 2, "fire": .5, "grass": .5, "poison": .5, "flying": .5, "bug": .5},
            "electric": {"water": 2, "flying": 2, "electric": .5, "grass": .5, "ground": 0},
            "bug": {"grass": 2, "psychic": 2, "dark": 2, "fire": .5, "fighting": .5, "flying": .5, "ghost": .5},
            "poison": {"grass": 2, "fairy": 2, "poison": .5, "ground": .5, "rock": .5, "ghost": .5, "steel": 0},
        }
        result = 1.0
        for defender_type in defender_types:
            result *= chart.get(move_type, {}).get(defender_type, 1.0)
        return result

    def apply_status_effect(self, move: dict, attacker: dict, defender: dict, state: dict) -> None:
        effect = move.get("effect")
        if effect == "lower_attack":
            stages = defender.setdefault("stat_stages", {"attack": 0, "defense": 0, "speed": 0})
            stages["attack"] = max(-6, stages["attack"] - 1)
            defender["attack"] = max(1, defender["attack"] - 1)
            state["log"].append(f'{defender["name"]} had its attack lowered!')
        elif effect == "paralyze_chance":
            if defender.get("status") is None and random.randint(1, 100) <= 20:
                defender["status"] = "paralyzed"
                state["log"].append(f'{defender["name"]} is paralyzed!')

    def resolve_move(self, attacker: dict, defender: dict, move_name: str, state: dict) -> None:
        from battle.wild_engine import WildTurnEngine
        from services.content_registry_v70 import ContentRegistryV70
        registry = ContentRegistryV70()
        if (registry.move(move_name) or {}).get('effect_id') == 154:
            state['log'].append('Teleport cannot end a trainer battle.')
            return
        for mon in (attacker, defender):
            data = registry.species(mon['name']) or {}
            mon.setdefault('level', 5)
            mon.setdefault('hp', 20)
            mon.setdefault('max_hp', mon['hp'])
            mon.setdefault('attack', 10)
            mon.setdefault('defense', 10)
            mon.setdefault('speed', 10)
            mon.setdefault('types', data.get('types', ['normal']))
            mon.setdefault('special_attack', data.get('base_special_attack', mon['attack']) + mon['level'])
            mon.setdefault('special_defense', data.get('base_special_defense', mon['defense']) + mon['level'])
            mon['stages'] = mon.setdefault('stat_stages', {})
        # Ranked battles have their own legal-move selection, rather than persisted PP slots.
        previous = attacker.get('moves')
        attacker['moves'] = [dict(name=move_name, pp=1, max_pp=1)]
        try:
            WildTurnEngine(registry, random).use(attacker, defender, move_name, state['log'])
        finally:
            if previous is None:
                attacker.pop('moves', None)
            else:
                attacker['moves'] = previous
