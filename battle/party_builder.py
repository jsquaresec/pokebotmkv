def pokemon_to_state(mon) -> dict:
    return {
        "pokemon_id": mon.id,
        "name": mon.species,
        "hp": mon.current_hp,
        "max_hp": mon.max_hp,
        "attack": mon.attack,
        "defense": mon.defense,
        "speed": mon.speed,
        "types": [t for t in [getattr(mon, "primary_type", "normal"), getattr(mon, "secondary_type", None)] if t],
        "level": getattr(mon, "level", 5),
        "stat_stages": {"attack": 0, "defense": 0, "speed": 0},
        "status": None,
    }

def build_team_state(team: list) -> dict:
    active = pokemon_to_state(team[0]) if team else None
    bench = [pokemon_to_state(mon) for mon in team[1:]] if len(team) > 1 else []
    return {
        "active_slot": 0,
        "active": active,
        "bench": bench,
    }
