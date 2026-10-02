import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from battle.wild_engine import WildTurnEngine, effectiveness
from models import Base, User, PokemonInstance, PartySlot, InventoryItem
from models.wild_encounter import WildEncounter
from services.content_registry_v70 import ContentRegistryV70
from services.wild_battle_service import WildBattleService, load_battle, save_battle
from services.encounter_v70_service import EncounterV70Service
from repositories.users import UserRepository
from repositories.inventory import InventoryRepository


class FixedRandom:
    def random(self):
        return .999

    def randint(self, low, high):
        return low

    def uniform(self, low, high):
        return high

    def choice(self, items):
        return items[0]


def fighter(name="Pikachu", hp=100, speed=50, moves=None):
    return dict(name=name, level=10, hp=hp, max_hp=100, attack=40, defense=30,
                special_attack=45, special_defense=35, speed=speed, types=["electric"],
                stages={}, status=None, moves=moves or [dict(name="Tackle", pp=35, max_pp=35)])


def test_type_chart_handles_dual_types_and_immunity():
    assert effectiveness("electric", ["ground"]) == 0
    assert effectiveness("ice", ["ground", "flying"]) == 4
    assert effectiveness("fighting", ["ghost", "steel"]) == 0
    assert effectiveness("dragon", ["fairy"]) == 0


def test_speed_priority_pp_and_fainting():
    engine = WildTurnEngine(ContentRegistryV70(), FixedRandom())
    player = fighter(speed=1, moves=[dict(name="Quick Attack", pp=1, max_pp=30)])
    wild = fighter("Wild", hp=1, speed=999)
    log = []
    engine.turn(player, wild, "Quick Attack", log)
    assert wild["hp"] == 0 and player["hp"] == 100
    assert player["moves"][0]["pp"] == 0
    assert wild["moves"][0]["pp"] == 35
    assert "Quick Attack" in log[0]


def test_faster_wild_can_prevent_player_move():
    engine = WildTurnEngine(ContentRegistryV70(), FixedRandom())
    player, wild = fighter(hp=1, speed=1), fighter("Wild", speed=999)
    engine.turn(player, wild, "Tackle", [])
    assert player["hp"] == 0
    assert player["moves"][0]["pp"] == 35


def test_stat_move_does_not_permanently_change_base_attack():
    engine = WildTurnEngine(ContentRegistryV70(), FixedRandom())
    player = fighter(moves=[dict(name="Growl", pp=40, max_pp=40)])
    wild = fighter("Wild")
    engine.use(player, wild, "Growl", [])
    assert wild["stages"]["attack"] == -1
    assert wild["attack"] == 40
    assert player["moves"][0]["pp"] == 39


def test_invalid_moves_and_struggle_rules():
    engine = WildTurnEngine(ContentRegistryV70(), FixedRandom())
    player, wild = fighter(), fighter("Wild")
    with pytest.raises(ValueError):
        engine.turn(player, wild, "Ember", [])
    with pytest.raises(ValueError):
        engine.turn(player, wild, "Struggle", [])
    player["moves"][0]["pp"] = 0
    engine.turn(player, wild, "Struggle", [])
    assert player["hp"] < 75 and wild["hp"] < 100


@pytest.fixture
async def battle_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add_all([User(id=1, discord_id=100, username="Trainer", balance=1000),
                         User(id=2, discord_id=200, username="Other", balance=1000)])
        for pid, species in ((1, "Pikachu"), (2, "Bulbasaur")):
            session.add(PokemonInstance(id=pid, owner_id=1, species=species, level=10,
                current_hp=100, max_hp=100, attack=40, defense=30, speed=40,
                primary_type="electric" if pid == 1 else "grass",
                moves_json=json.dumps([dict(name="Tackle", pp=35, max_pp=35)])))
            session.add(PartySlot(owner_id=1, pokemon_id=pid, slot_index=pid))
        session.add_all([InventoryItem(owner_discord_id=100, sku="poke_ball", quantity=3),
                         InventoryItem(owner_discord_id=100, sku="master_ball", quantity=1)])
        session.add(WildEncounter(id=1, guild_id=1, channel_id=2, species="Pikachu", level=5,
                                  current_hp=1000, max_hp=1000, expires_at=datetime.utcnow()+timedelta(minutes=5)))
        await session.commit()
        yield session
    await engine.dispose()


async def begin(session):
    service = WildBattleService(session, rng=FixedRandom())
    row = await service.apply(1, 2, 100, "start")
    # Test retaliation with a known damaging move, independent of catalog learnset ordering.
    state = load_battle(row)
    state['wild']['moves'] = [dict(name='Tackle', pp=35, max_pp=35)]
    save_battle(row, 100, state)
    await session.commit()
    return service, row


async def test_battle_turn_persists_both_hp_and_pp(battle_db):
    service, row = await begin(battle_db)
    assert (await battle_db.get(PokemonInstance, 1)).locked
    await service.apply(1, 2, 100, "move", "Tackle", 1)
    await battle_db.commit()
    await battle_db.refresh(row)
    state = load_battle(row)
    mon = await battle_db.get(PokemonInstance, 1)
    assert state["turn"] == 2 and state["wild"]["hp"] < 1000
    assert mon.current_hp < 100 and json.loads(mon.moves_json)[0]["pp"] == 34
    assert state["team"][0]["hp"] == mon.current_hp
    assert load_battle(row)["owner"] == 100


async def test_failed_ball_spends_inventory_and_wild_takes_turn(battle_db):
    service, row = await begin(battle_db)
    await service.apply(1, 2, 100, "ball", "poke_ball", 1)
    await battle_db.commit()
    assert (await InventoryRepository(battle_db).get_item(100, "poke_ball")).quantity == 2
    assert (await battle_db.get(PokemonInstance, 1)).current_hp < 100
    assert (await battle_db.get(User, 1)).balance == 1000
    assert not load_battle(row)["finished"]


async def test_catch_rewards_once_and_unlocks_party(battle_db):
    service, row = await begin(battle_db)
    await service.apply(1, 2, 100, "ball", "master_ball", 1)
    await battle_db.commit()
    assert row.status == "open"
    assert load_battle(row, 100)["result"] == "caught"
    assert (await battle_db.get(User, 1)).balance == 1500
    assert not (await battle_db.get(PokemonInstance, 1)).locked
    assert not (await battle_db.get(PokemonInstance, 2)).locked
    assert (await battle_db.get(PokemonInstance, 1)).current_hp == 100
    with pytest.raises(ValueError):
        await service.apply(1, 2, 100, "ball", "master_ball", 1)


async def test_other_player_and_legacy_catch_cannot_steal(battle_db):
    service, row = await begin(battle_db)
    with pytest.raises(ValueError):
        await service.apply(1, 2, 200, "start")
    with pytest.raises(ValueError):
        await service.apply(1, 2, 200, "move", "Tackle", 1)
    with pytest.raises(ValueError):
        await EncounterV70Service(battle_db).attempt_catch(2, 200, "master_ball", UserRepository(battle_db), InventoryRepository(battle_db))


async def test_stale_turn_does_not_spend_pp_twice(battle_db):
    service, row = await begin(battle_db)
    await service.apply(1, 2, 100, "move", "Tackle", 1)
    await battle_db.commit()
    snapshot = row.battle_state_json
    await service.apply(1, 2, 100, "move", "Tackle", 1)
    assert row.battle_state_json == snapshot


async def test_forced_switch_has_no_free_enemy_hit(battle_db):
    service, row = await begin(battle_db)
    state = load_battle(row)
    state["team"][0]["hp"] = 0
    save_battle(row, 100, state)
    (await battle_db.get(PokemonInstance, 1)).current_hp = 0
    await battle_db.commit()
    await service.apply(1, 2, 100, "switch", 1, 1)
    assert load_battle(row)["active"] == 1
    assert (await battle_db.get(PokemonInstance, 2)).current_hp == 100


async def test_run_and_expiry_release_party(battle_db):
    service, row = await begin(battle_db)
    await service.apply(1, 2, 100, "run", expected_turn=1)
    await battle_db.commit()
    assert row.status == "open" and load_battle(row, 100)["result"] == "ran"
    assert not (await battle_db.get(PokemonInstance, 1)).locked
    # Reuse a fresh encounter to verify offline expiry cleanup.
    battle_db.add(WildEncounter(id=2, guild_id=1, channel_id=2, species="Pikachu", level=5,
        current_hp=100, max_hp=100, expires_at=datetime.utcnow()+timedelta(minutes=5)))
    await battle_db.commit()
    fresh = await service.apply(2, 2, 100, "start")
    fresh.expires_at = datetime.utcnow()-timedelta(seconds=1)
    await battle_db.commit()
    await WildBattleService.expire(battle_db)
    await battle_db.commit()
    assert fresh.status == "expired" and not (await battle_db.get(PokemonInstance, 1)).locked
    assert (await battle_db.get(User, 1)).balance == 1000


async def test_knockout_awards_xp_and_250_gold_once(battle_db):
    service, row = await begin(battle_db)
    state = load_battle(row)
    state["wild"]["hp"] = 1
    row.current_hp = 1
    save_battle(row, 100, state)
    await battle_db.commit()
    await service.apply(1, 2, 100, "move", "Tackle", 1)
    await battle_db.commit()
    assert row.status == "open"
    assert load_battle(row, 100)["result"] == "won"
    assert (await battle_db.get(User, 1)).balance == 1250
    assert (await battle_db.get(PokemonInstance, 1)).experience > 1000
    assert not (await battle_db.get(PokemonInstance, 1)).locked
    from core.wild_battle_view import battle_card
    fields = {field.name: field.value for field in battle_card(row, owner_id=100).fields}
    assert fields['Battle reward'] == '**+250 gold**'
    assert fields['Gold remaining'] == '**1,250 gold**'
    with pytest.raises(ValueError, match='Only the trainer'):
        await service.apply(1, 2, 100, 'move', 'Tackle', 1)
    assert (await battle_db.get(User, 1)).balance == 1250


async def test_losing_a_wild_battle_does_not_award_gold(battle_db):
    service, row = await begin(battle_db)
    state = load_battle(row)
    for mon in state['team']:
        mon['hp'] = 0
    state['team'][0]['hp'] = 1
    state['wild']['speed'] = 999
    save_battle(row, 100, state)
    await battle_db.commit()
    await service.apply(1, 2, 100, 'move', 'Tackle', 1)
    await battle_db.commit()
    assert load_battle(row)['result'] == 'lost'
    assert (await battle_db.get(User, 1)).balance == 1000


async def test_battle_view_updates_same_card_without_followups(battle_db):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, Mock
    from core.wild_battle_view import WildBattleView, battle_card
    service, row = await begin(battle_db)
    async def action(interaction, encounter_id, kind, value, turn):
        updated = await service.apply(encounter_id, 2, 100, kind, value, turn)
        await battle_db.commit()
        return updated
    view = WildBattleView(row, action)
    from gui_fakes import interaction as fake_interaction, message
    interaction = fake_interaction(user_id=100, source=message(owner=100))
    await view.children[0].callback(interaction)
    interaction.response.defer.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()
    interaction.followup.send.assert_not_awaited()
    assert "34/35" in view.children[0].label
    embed = battle_card(row)
    assert any("Your Pokémon" in field.name for field in embed.fields)
    assert any(field.name == "Battle log" for field in embed.fields)


async def test_empty_and_completed_cards_render(battle_db):
    from core.wild_battle_view import WildBattleView, battle_card
    from unittest.mock import AsyncMock
    row = await battle_db.get(WildEncounter, 1)
    view = WildBattleView(row, AsyncMock())
    assert len(view.children) == 2 and "Battle" in view.children[0].label
    assert len(battle_card(row)) < 6000
    service, row = await begin(battle_db)
    await service.apply(1, 2, 100, "ball", "master_ball", 1)
    view = WildBattleView(row, AsyncMock())
    assert all(button.disabled for button in view.children if button.label != 'Home')
    assert "caught" in battle_card(row, owner_id=100).title.lower()


@pytest.mark.parametrize('result,status', [('won','defeated'), ('caught','caught'), ('lost','fled'), ('ran','fled'), ('expired','expired')])
async def test_finished_battle_has_home_only_and_returns_to_private_dashboard(battle_db, result, status):
    from core.wild_battle_view import WildBattleView
    from unittest.mock import AsyncMock
    from gui_fakes import interaction, message
    _, row = await begin(battle_db)
    state = load_battle(row)
    state.update(finished=True, result=result)
    save_battle(row, 100, state)
    row.status = status
    view = WildBattleView(row, AsyncMock(), 100)
    assert len(view.children) == 1
    home = view.children[0]
    assert home.label == 'Home' and not home.disabled
    assert view.timeout == 300
    click = interaction(user_id=100, source=message(owner=100))
    await home.callback(click)
    click.response.edit_message.assert_awaited_once()
    assert 'Adventure Hub' in click.response.edit_message.call_args.kwargs['embeds'][0].title
    click.followup.send.assert_not_awaited()
