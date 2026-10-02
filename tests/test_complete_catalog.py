import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from models import PokemonInstance
from services.catalog_upgrade_service import CatalogUpgradeService
from services.content_registry_v70 import ContentRegistryV70
from services.moveset_v80_service import MovesetV80Service
from services.pokemon_traits_service import PokemonTraitsService
from services.progression_v70_service import ProgressionV70Service
from battle.wild_engine import WildTurnEngine
from test_wild_battles import battle_db, fighter, FixedRandom


def test_entire_roster_has_real_species_data_and_resolvable_learnsets():
    registry = ContentRegistryV70()
    assert registry.validate() == []
    names = registry.all_species()
    assert len(names) == 1025
    ids = set()
    for name in names:
        species = registry.species(name)
        ids.add(species['dex_number'])
        assert species['abilities'] and species['learnset_version'], name
        assert 1 <= len(species['types']) <= 2, name
        assert 0 < species['catch_rate'] <= 255, name
        for stat in ('hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed'):
            assert 0 < species['base_' + stat] <= 255, (name, stat)
        assert registry.legal_moves(name, 100, supported_only=False), name
        for level in (2, 5, 25, 50, 100):
            mon = SimpleNamespace(species=name, level=level, moves_json='[]')
            slots = MovesetV80Service().initialize(mon, registry)
            assert len(slots) <= 4
            for slot in slots:
                assert registry.move(slot['name'])['battle_supported']
                assert slot['pp'] == slot['max_pp'] > 0
    assert ids == set(range(1, 1026))


def test_yamper_and_special_names_are_correct():
    registry = ContentRegistryV70()
    yamper = registry.species('yamper')
    assert yamper['dex_number'] == 835
    assert yamper['types'] == ['electric']
    assert yamper['base_hp'] == 59 and yamper['base_speed'] == 26
    assert yamper['evolves_to'] == 'Boltund' and yamper['evolution_level'] == 25
    assert [a['name'] for a in yamper['abilities'] if not a['hidden']] == ['Ball Fetch']
    assert 'Nuzzle' in registry.legal_moves('Yamper', 5)
    assert 'Nuzzle' not in registry.legal_moves('Yamper', 4)
    for name, dex in [('Nidoran♀',29), ('Nidoran♂',32), ('Farfetch’d',83), ('Flabébé',669), ('Sirfetch’d',865)]:
        assert registry.species(name)['dex_number'] == dex


def test_catalog_manifest_matches_generated_files():
    manifest = json.loads(Path('data/catalog_manifest.json').read_text(encoding='utf-8'))
    assert len(manifest['revision']) == 40
    for filename, digest in manifest['files'].items():
        assert hashlib.sha256((Path('data') / filename).read_bytes()).hexdigest() == digest


def test_unsupported_mechanics_are_not_silently_replaced():
    registry = ContentRegistryV70()
    assert 'Transform' in registry.legal_moves('Ditto', 100, supported_only=False)
    assert 'Transform' not in registry.legal_moves('Ditto', 100)
    with pytest.raises(ValueError, match='special mechanics'):
        WildTurnEngine(registry).move('Transform')
    with pytest.raises(ValueError, match='Unknown move'):
        MovesetV80Service._slot('Fake Move', registry)


def test_every_supported_move_resolves_with_bounded_hp_and_spends_pp():
    registry = ContentRegistryV70()
    engine = WildTurnEngine(registry, FixedRandom())
    for move in registry._moves.values():
        if not move['battle_supported']:
            continue
        player = fighter(moves=[dict(name=move['name'], pp=move['pp'], max_pp=move['pp'])])
        player['hp'] = 50
        target = fighter('Target')
        target['types'] = ['water']
        engine.use(player, target, move['name'], [])
        assert player['moves'][0]['pp'] == move['pp'] - 1, move['name']
        assert 0 <= player['hp'] <= player['max_hp'], move['name']
        assert 0 <= target['hp'] <= target['max_hp'], move['name']


def test_nuzzle_healing_and_multi_stat_moves():
    registry = ContentRegistryV70()
    engine = WildTurnEngine(registry, FixedRandom())
    player = fighter(moves=[dict(name='Nuzzle', pp=20, max_pp=20)])
    target = fighter('Target')
    target['types'] = ['water']
    engine.use(player, target, 'Nuzzle', [])
    assert target['status'] == 'paralyzed' and target['hp'] < 100
    player['hp'] = 10
    player['moves'] = [dict(name='Recover', pp=5, max_pp=5)]
    engine.use(player, target, 'Recover', [])
    assert player['hp'] == 60
    player['moves'] = [dict(name='Cosmic Power', pp=20, max_pp=20)]
    engine.use(player, target, 'Cosmic Power', [])
    assert player['stages'] == {'defense':1, 'special_defense':1}


def test_species_abilities_and_gender_restrictions():
    registry = ContentRegistryV70()
    traits = PokemonTraitsService(FixedRandom())
    assert traits.roll(['electric'], registry.species('Yamper'))['ability'] == 'Ball Fetch'
    assert traits.roll(['electric'], registry.species('Magnemite'))['gender'] == 'genderless'
    assert traits.roll(['poison'], registry.species('Nidoran♀'))['gender'] == 'female'


async def test_existing_fainted_pokemon_upgrade_preserves_zero_hp_and_pp(battle_db):
    mon = await battle_db.get(PokemonInstance, 1)
    mon.species, mon.catalog_revision, mon.current_hp = 'Yamper', 0, 0
    mon.ability = 'Adaptability'
    mon.moves_json = json.dumps([dict(name='Tackle',pp=0,max_pp=35)])
    assert CatalogUpgradeService().upgrade(mon)
    await battle_db.commit()
    await battle_db.refresh(mon)
    assert mon.dex_number == 835 and mon.primary_type == 'electric'
    assert mon.ability == 'Ball Fetch' and mon.current_hp == 0
    assert json.loads(mon.moves_json)[0]['pp'] == 0
    assert not CatalogUpgradeService().upgrade(mon)


async def test_catalog_upgrade_skips_locked_pokemon_and_can_resume(battle_db):
    mon = await battle_db.get(PokemonInstance, 1)
    mon.catalog_revision, mon.locked = 0, True
    await battle_db.commit()
    service = CatalogUpgradeService()
    assert await service.upgrade_available(battle_db) == 0
    assert mon.catalog_revision == 0
    mon.locked = False
    await battle_db.flush()
    assert await service.upgrade_available(battle_db) == 1
    await battle_db.commit()
    assert mon.catalog_revision == 1


async def test_yamper_evolution_updates_stats_and_ability_without_reviving(battle_db):
    mon = await battle_db.get(PokemonInstance, 1)
    mon.species, mon.level, mon.current_hp, mon.ability = 'Yamper', 25, 0, 'Ball Fetch'
    ProgressionV70Service().evolve(mon, ContentRegistryV70())
    await battle_db.commit()
    assert mon.species == 'Boltund' and mon.dex_number == 836
    assert mon.ability == 'Strong Jaw' and mon.current_hp == 0
