"""Turn mechanics for wild encounters using the installed move catalog."""
import random


TYPE_CHART = {
    "normal": ({}, {"rock", "steel"}, {"ghost"}),
    "fire": ({"grass", "ice", "bug", "steel"}, {"fire", "water", "rock", "dragon"}, set()),
    "water": ({"fire", "ground", "rock"}, {"water", "grass", "dragon"}, set()),
    "electric": ({"water", "flying"}, {"electric", "grass", "dragon"}, {"ground"}),
    "grass": ({"water", "ground", "rock"}, {"fire", "grass", "poison", "flying", "bug", "dragon", "steel"}, set()),
    "ice": ({"grass", "ground", "flying", "dragon"}, {"fire", "water", "ice", "steel"}, set()),
    "fighting": ({"normal", "ice", "rock", "dark", "steel"}, {"poison", "flying", "psychic", "bug", "fairy"}, {"ghost"}),
    "poison": ({"grass", "fairy"}, {"poison", "ground", "rock", "ghost"}, {"steel"}),
    "ground": ({"fire", "electric", "poison", "rock", "steel"}, {"grass", "bug"}, {"flying"}),
    "flying": ({"grass", "fighting", "bug"}, {"electric", "rock", "steel"}, set()),
    "psychic": ({"fighting", "poison"}, {"psychic", "steel"}, {"dark"}),
    "bug": ({"grass", "psychic", "dark"}, {"fire", "fighting", "poison", "flying", "ghost", "steel", "fairy"}, set()),
    "rock": ({"fire", "ice", "flying", "bug"}, {"fighting", "ground", "steel"}, set()),
    "ghost": ({"psychic", "ghost"}, {"dark"}, {"normal"}),
    "dragon": ({"dragon"}, {"steel"}, {"fairy"}),
    "dark": ({"psychic", "ghost"}, {"fighting", "dark", "fairy"}, set()),
    "steel": ({"ice", "rock", "fairy"}, {"fire", "water", "electric", "steel"}, set()),
    "fairy": ({"fighting", "dragon", "dark"}, {"fire", "poison", "steel"}, set()),
}
STRUGGLE = {"name": "Struggle", "power": 50, "type": "typeless", "category": "physical", "accuracy": 100}


def effectiveness(move_type, types):
    strong, weak, immune = TYPE_CHART.get(move_type, (set(), set(), set()))
    result = 1.0
    for kind in types:
        result *= 0 if kind in immune else 2 if kind in strong else 0.5 if kind in weak else 1
    return result


def stage(value):
    value = max(-6, min(6, value))
    return (2 + value) / 2 if value >= 0 else 2 / (2 - value)


class WildTurnEngine:
    def __init__(self, registry, rng=None):
        self.registry, self.rng = registry, rng or random.Random()

    def available(self, mon):
        return [slot for slot in mon["moves"] if slot["pp"] > 0 and
                (self.registry.move(slot['name']) or {}).get('battle_supported', False)]

    def move(self, name):
        move = STRUGGLE if name == "Struggle" else self.registry.move(name)
        if not move:
            raise ValueError("That move is not supported.")
        if not move.get('battle_supported', True):
            raise ValueError("That move's special mechanics are not available in battles yet.")
        return move

    def speed(self, mon):
        return mon["speed"] * stage(mon["stages"].get("speed", 0)) * (0.5 if mon.get("status") == "paralyzed" else 1)

    def priority(self, name):
        move = self.move(name)
        return move.get("priority", 1 if move.get("effect") == "priority" else 0)

    def use(self, attacker, defender, name, log):
        if attacker["hp"] <= 0 or defender["hp"] <= 0:
            return
        if attacker.pop('flinch', False):
            log.append(f'{attacker["name"]} flinched!')
            return
        if attacker.get('status') == 'frozen':
            if self.rng.random() >= .2:
                log.append(f'{attacker["name"]} is frozen solid!')
                return
            attacker['status'] = None
            log.append(f'{attacker["name"]} thawed out!')
        if attacker.get("sleep", 0) > 0:
            attacker["sleep"] -= 1
            if attacker["sleep"]:
                log.append(f'{attacker["name"]} is asleep.')
                return
            attacker["status"] = None
            log.append(f'{attacker["name"]} woke up!')
        if attacker.get("status") == "paralyzed" and self.rng.random() < .25:
            log.append(f'{attacker["name"]} is fully paralyzed!')
            return
        if attacker.get('confusion', 0):
            attacker['confusion'] -= 1
            if attacker['confusion'] and self.rng.random() < 1 / 3:
                damage = max(1, int(((2 * attacker['level'] / 5 + 2) * 40 * attacker['attack'] / max(1, attacker['defense'])) / 50 + 2))
                attacker['hp'] = max(0, attacker['hp'] - damage)
                log.append(f'{attacker["name"]} hurt itself in confusion!')
                return
        move = self.move(name)
        if name != "Struggle":
            slot = next((s for s in attacker["moves"] if s["name"] == name and s["pp"] > 0), None)
            if not slot:
                raise ValueError("That move has no PP left.")
            slot["pp"] -= 1
        log.append(f'{attacker["name"]} used {name}!')
        accuracy = move.get('accuracy')
        accuracy_stage = max(-6, min(6, attacker['stages'].get('accuracy', 0) - defender['stages'].get('evasion', 0)))
        accuracy_factor = (3 + accuracy_stage) / 3 if accuracy_stage >= 0 else 3 / (3 - accuracy_stage)
        if accuracy is not None and self.rng.randint(1, 100) > accuracy * accuracy_factor:
            log.append("The move missed!")
            return
        if 'effect_id' in move:
            self.catalog_effect(attacker, defender, move, log)
            return
        multiplier = effectiveness(move.get("type", "normal"), defender["types"])
        if move.get("power", 0) > 0:
            special = move["category"] == "special"
            atk_key, def_key = ("special_attack", "special_defense") if special else ("attack", "defense")
            attack = attacker[atk_key] * stage(attacker["stages"].get(atk_key, 0))
            defense = max(1, defender[def_key] * stage(defender["stages"].get(def_key, 0)))
            base = ((2 * attacker["level"] / 5 + 2) * move["power"] * attack / defense) / 50 + 2
            stab = 1.5 if move.get("type") in attacker["types"] else 1
            crit = self.rng.random() < 1 / 24
            burn = .5 if not special and attacker.get("status") == "burned" else 1
            damage = max(1, int(base * stab * multiplier * (1.5 if crit else 1) * burn * self.rng.uniform(.85, 1))) if multiplier else 0
            defender["hp"] = max(0, defender["hp"] - damage)
            log.append(f'{defender["name"]} took {damage} damage.')
            if multiplier == 0:
                log.append("It had no effect.")
            elif multiplier > 1:
                log.append("It's super effective!")
            elif multiplier < 1:
                log.append("It's not very effective.")
            if crit and multiplier:
                log.append("A critical hit!")
            if name == "Struggle":
                attacker["hp"] = max(0, attacker["hp"] - max(1, attacker["max_hp"] // 4))
                log.append(f'{attacker["name"]} took recoil damage.')
        effect = move.get("effect")
        if effect in ("lower_attack", "lower_defense"):
            key = "attack" if effect == "lower_attack" else "defense"
            defender["stages"][key] = max(-6, defender["stages"].get(key, 0) - 1)
            log.append(f'{defender["name"]}\'s {key} fell!')
        statuses = {"paralyze_chance": ("paralyzed", .2), "paralyze": ("paralyzed", 1),
                    "burn_chance": ("burned", .1), "poison_chance": ("poisoned", .3), "sleep": ("asleep", 1)}
        if effect in statuses and defender["hp"] > 0 and not defender.get("status") and multiplier:
            status, chance = statuses[effect]
            immune = ((status == "paralyzed" and "electric" in defender["types"])
                      or (status == "burned" and "fire" in defender["types"])
                      or (status == "poisoned" and any(t in defender["types"] for t in ("poison", "steel")))
                      or (status == "asleep" and "grass" in defender["types"]))
            if not immune and self.rng.random() < chance:
                defender["status"] = status
                if status == "asleep":
                    defender["sleep"] = self.rng.randint(2, 4)
                log.append(f'{defender["name"]} is {status}!')
        if defender["hp"] == 0:
            log.append(f'{defender["name"]} fainted!')

    def catalog_effect(self, attacker, defender, move, log):
        """Resolve only reviewed catalog effects; unsupported moves are rejected by move()."""
        effect = move['effect_id']
        meta = move.get('meta', {})
        multiplier = effectiveness(move['type'], defender['types'])
        damage = 0
        if effect == 154:
            attacker['escaped'] = True
            log.append(f'{attacker["name"]} teleported away!')
            return
        if effect == 26:
            attacker['stages'].clear()
            defender['stages'].clear()
            log.append('All stat changes were reset.')
            return
        if effect == 86:
            log.append('But nothing happened!')
            return
        if effect == 92:
            hp = (attacker['hp'] + defender['hp']) // 2
            attacker['hp'] = min(attacker['max_hp'], hp)
            defender['hp'] = min(defender['max_hp'], hp)
            log.append('The two Pokémon shared their remaining HP.')
            return
        if effect in (41, 42, 88, 89, 90, 145):
            damage = {41: max(1, defender['hp'] // 2), 42: 40, 88: attacker['level'],
                      89: int(attacker['level'] * self.rng.uniform(.5, 1.5)),
                      90: 2 * attacker.get('physical_damage_taken', 0),
                      145: 2 * attacker.get('special_damage_taken', 0)}[effect] if multiplier else 0
        elif move['power'] > 0 or effect == 100:
            special = move['category'] == 'special'
            atk, defense = ('special_attack', 'special_defense') if special else ('attack', 'defense')
            a = attacker[atk] * stage(attacker['stages'].get(atk, 0))
            d = max(1, defender[defense] * stage(defender['stages'].get(defense, 0)))
            power = move['power']
            if effect == 100:
                ratio = 48 * attacker['hp'] // attacker['max_hp']
                power = 200 if ratio < 2 else 150 if ratio < 5 else 100 if ratio < 10 else 80 if ratio < 17 else 40 if ratio < 33 else 20
            base = ((2 * attacker['level'] / 5 + 2) * power * a / d) / 50 + 2
            stab = 1.5 if move['type'] in attacker['types'] else 1
            crit = self.rng.random() < (1 / 8 if (meta.get('crit_rate') or 0) else 1 / 24)
            burn = .5 if not special and attacker.get('status') == 'burned' else 1
            damage = max(1, int(base * stab * multiplier * (1.5 if crit else 1) * burn * self.rng.uniform(.85, 1))) if multiplier else 0
            hits = self.rng.randint(meta['min_hits'], meta['max_hits']) if meta.get('min_hits') else 1
            damage *= hits
            if hits > 1:
                log.append(f'Hit {hits} times!')
            if crit and multiplier:
                log.append('A critical hit!')
        if move['category'] != 'status':
            damage = min(defender['hp'], damage)
            defender['hp'] -= damage
            if move['category'] == 'physical':
                defender['physical_damage_taken'] = damage
            else:
                defender['special_damage_taken'] = damage
            log.append(f'{defender["name"]} took {damage} damage.')
            if not multiplier:
                log.append('It had no effect.')
            elif multiplier > 1:
                log.append("It's super effective!")
            elif multiplier < 1:
                log.append("It's not very effective.")
        drain = meta.get('drain') or 0
        if damage and drain:
            change = max(1, int(damage * abs(drain) / 100))
            attacker['hp'] = min(attacker['max_hp'], attacker['hp'] + change) if drain > 0 else max(0, attacker['hp'] - change)
            log.append(f'{attacker["name"]} {"recovered HP" if drain > 0 else "took recoil damage"}.')
        if meta.get('healing'):
            attacker['hp'] = min(attacker['max_hp'], attacker['hp'] + max(1, attacker['max_hp'] * meta['healing'] // 100))
            log.append(f'{attacker["name"]} recovered HP!')
        changes = move.get('stat_changes', [])
        chance = meta.get('stat_chance') or (100 if move['category'] == 'status' else move.get('effect_chance', 0))
        if changes and self.rng.random() < chance / 100:
            target = attacker if move['target'] in ('user', 'user-and-allies') or meta.get('meta_category_id') == 7 else defender
            if target is attacker or (defender['hp'] and (multiplier or move['category'] == 'status')):
                for change in changes:
                    key = change['stat']
                    target['stages'][key] = max(-6, min(6, target['stages'].get(key, 0) + change['change']))
                    log.append(f'{target["name"]}\'s {key.replace("_", " ")} {"rose" if change["change"] > 0 else "fell"}!')
        status = {1:'paralyzed', 2:'asleep', 3:'frozen', 4:'burned', 5:'poisoned'}.get(meta.get('meta_ailment_id'))
        chance = meta.get('ailment_chance') or (100 if move['category'] == 'status' else 0)
        immune = ((status == 'paralyzed' and 'electric' in defender['types']) or
                  (status == 'burned' and 'fire' in defender['types']) or
                  (status == 'frozen' and 'ice' in defender['types']) or
                  (status == 'poisoned' and any(t in defender['types'] for t in ('poison', 'steel'))) or
                  ('grass' in defender['types'] and ('Powder' in move['name'] or move['name'] == 'Spore')))
        type_blocks_status = move['name'] in ('Thunder Wave',) and not multiplier
        if meta.get('meta_ailment_id') == 6 and defender['hp'] > 0 and not defender.get('confusion') and multiplier and self.rng.random() < chance / 100:
            defender['confusion'] = self.rng.randint(2, 5)
            log.append(f'{defender["name"]} became confused!')
        if status and defender['hp'] > 0 and not defender.get('status') and not immune and not type_blocks_status and (multiplier or move['category'] == 'status') and self.rng.random() < chance / 100:
            defender['status'] = status
            if status == 'asleep':
                defender['sleep'] = self.rng.randint(2, 4)
            log.append(f'{defender["name"]} is {status}!')
        if damage and self.rng.random() < (meta.get('flinch_chance') or 0) / 100:
            defender['flinch'] = True
        if defender['hp'] == 0:
            log.append(f'{defender["name"]} fainted!')

    def enemy_move(self, wild):
        available = self.available(wild)
        return self.rng.choice(available)["name"] if available else "Struggle"

    def turn(self, active, wild, chosen, log):
        for mon in (active, wild):
            mon.pop('flinch', None)
            mon['physical_damage_taken'] = 0
            mon['special_damage_taken'] = 0
        available = self.available(active)
        if chosen == "Struggle":
            if available:
                raise ValueError("Use one of your moves while it still has PP.")
        elif not any(slot["name"] == chosen for slot in available):
            raise ValueError("Choose a learned move with PP remaining.")
        enemy = self.enemy_move(wild)
        player_first = (self.priority(chosen), self.speed(active)) > (self.priority(enemy), self.speed(wild))
        if (self.priority(chosen), self.speed(active)) == (self.priority(enemy), self.speed(wild)):
            player_first = self.rng.random() < .5
        turns = [(active, wild, chosen), (wild, active, enemy)]
        if not player_first:
            turns.reverse()
        for attacker, defender, name in turns:
            self.use(attacker, defender, name, log)
            if attacker.get('escaped'):
                return
        self.residual(active, wild, log)

    def residual(self, active, wild, log):
        if active["hp"] <= 0 or wild["hp"] <= 0:
            return
        for mon in (active, wild):
            if mon.get("status") in ("burned", "poisoned"):
                damage = max(1, mon["max_hp"] // (16 if mon["status"] == "burned" else 8))
                mon["hp"] = max(0, mon["hp"] - damage)
                log.append(f'{mon["name"]} lost {damage} HP to {mon["status"]}.')
