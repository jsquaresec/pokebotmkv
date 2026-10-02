from types import SimpleNamespace
from battle.move_engine import MoveEngine
from services.content_registry_v70 import ContentRegistryV70
from services.encounter_v70_service import EncounterV70Service
from services.progression_v70_service import ProgressionV70Service


def test_content_registry_is_valid_and_complete():
    registry = ContentRegistryV70()
    assert len(registry.all_species()) >= 1000
    assert registry.species("Pikachu")["types"] == ["electric"]
    assert registry.validate() == []


def test_type_effectiveness():
    engine = MoveEngine()
    assert engine.type_multiplier("electric", ["water"]) == 2
    assert engine.type_multiplier("electric", ["ground"]) == 0


def test_low_hp_increases_catch_chance():
    service = object.__new__(EncounterV70Service)
    service.registry = ContentRegistryV70()
    full = SimpleNamespace(species="Pikachu", current_hp=100, max_hp=100)
    low = SimpleNamespace(species="Pikachu", current_hp=1, max_hp=100)
    assert service.catch_probability(low, "poke_ball") > service.catch_probability(full, "poke_ball")
    assert service.catch_probability(full, "master_ball") == 1


def test_progression_and_evolution_readiness():
    mon = SimpleNamespace(species="Bulbasaur", level=15, experience=15**3, max_hp=50, current_hp=50, attack=20, defense=20, speed=20)
    result = ProgressionV70Service().grant_experience(mon, 16**3 - 15**3, ContentRegistryV70())
    assert mon.level == 16
    assert result["can_evolve_to"] == "Ivysaur"
