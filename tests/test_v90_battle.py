from types import SimpleNamespace
from services.battle_service import BattleService


def mon(id, hp=20):
    return SimpleNamespace(id=id, species="Pikachu", current_hp=hp, max_hp=20,
                           attack=12, defense=10, speed=10, level=5)


def test_bench_keeps_owner_and_does_not_attack_after_replacement():
    service = BattleService(None)
    state = service._build_state(100, 200, [mon(1)], [mon(2, 1), mon(3)])
    assert state["player_two"]["bench"][0]["discord_id"] == 200
    calls = []
    def damage(attacker, defender, move, state):
        calls.append(attacker["pokemon_id"])
        defender["hp"] = 0
    service.engine.move_engine.resolve_move = damage
    service.engine.resolve_turn(state)
    assert calls == [1]
    assert state["player_two"]["active"]["pokemon_id"] == 3
