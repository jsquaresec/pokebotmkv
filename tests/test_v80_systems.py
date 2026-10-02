import json
from types import SimpleNamespace
import pytest
from services.moveset_v80_service import MovesetV80Service
from services.pokemon_traits_service import NATURES, PokemonTraitsService
from services.season_pass_service import SeasonPassService
from services.system_health_v80_service import SystemHealthV80Service
from services.trainer_progression_service import TrainerProgressionService


class Registry:
    def legal_moves(self, species, level):
        return ["Tackle", "Growl", "Quick Attack", "Thunder Shock", "Vine Whip"]

    def move(self, name):
        return {"name": name, "pp": 20}


def test_natures_have_bounded_multipliers():
    for nature in NATURES:
        for stat in ("attack", "defense", "speed"):
            assert PokemonTraitsService.nature_multiplier(nature, stat) in {0.9, 1.0, 1.1}


def test_moveset_enforces_four_slots_and_replacement():
    mon = SimpleNamespace(species="Pikachu", level=50, moves_json="[]")
    service = MovesetV80Service()
    service.initialize(mon, Registry())
    assert len(json.loads(mon.moves_json)) == 4
    with pytest.raises(ValueError):
        service.learn(mon, "Vine Whip", Registry())
    service.learn(mon, "Tackle", Registry(), replace_index=1)
    assert json.loads(mon.moves_json)[0]["name"] == "Tackle"


def test_trainer_progression_carries_xp():
    user = SimpleNamespace(trainer_level=1, trainer_xp=0, season_xp=0)
    gained = TrainerProgressionService().grant(user, 150)
    assert gained == 1
    assert user.trainer_level == 2
    assert user.trainer_xp == 50
    assert user.season_xp == 150


@pytest.mark.parametrize("xp,tier", [(0, 0), (499, 0), (500, 1), (2500, 5), (9999, 5)])
def test_season_tiers(xp, tier):
    assert SeasonPassService.tier(xp) == tier


def test_v80_health_snapshot():
    result = SystemHealthV80Service.snapshot()
    assert result["version"] == "90.0.0"
    assert result["status"] == "content-valid"
    assert result["species"] >= 1000


def test_debug_api_routes_are_disabled_by_default():
    from api.dashboard import app

    routes = {route.path for route in app.routes}
    assert "/queue/status" not in routes
    assert "/admin/ops/queue/reset" not in routes
