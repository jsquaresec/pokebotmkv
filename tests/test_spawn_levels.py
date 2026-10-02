from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from models import PokemonInstance, PartySlot
from services.encounter_v70_service import EncounterV70Service
from services.content_registry_v70 import ContentRegistryV70
from test_wild_battles import battle_db


class BoundRandom:
    def __init__(self, upper=False):
        self.upper = upper
        self.bounds = None

    def choice(self, values):
        return 'Yamper'

    def randint(self, low, high):
        self.bounds = (low, high)
        return high if self.upper else low


@pytest.mark.parametrize('level,bounds', [(1,(1,3)), (2,(1,4)), (5,(3,7)), (25,(23,27)), (99,(97,100)), (100,(98,100))])
@pytest.mark.parametrize('upper', [False, True])
async def test_spawn_uses_leader_level_and_derives_hp(battle_db, level, bounds, upper):
    leader = await battle_db.get(PokemonInstance, 1)
    leader.level, leader.current_hp = level, 0
    bench = await battle_db.get(PokemonInstance, 2)
    bench.level = 80
    await battle_db.commit()
    rng = BoundRandom(upper)
    row = await EncounterV70Service(battle_db, rng=rng).spawn(1, 10, 100)
    await battle_db.commit()
    assert rng.bounds == bounds
    assert row.level == bounds[1 if upper else 0]
    expected_hp = ContentRegistryV70().species('Yamper')['base_hp'] + row.level * 2
    assert row.current_hp == row.max_hp == expected_hp
    # Once posted, leveling or reordering a party does not change the wild spawn.
    leader.level = 60
    await battle_db.commit()
    await battle_db.refresh(row)
    assert row.level == bounds[1 if upper else 0]
    second = await EncounterV70Service(battle_db, rng=rng).spawn(1, 10, 100)
    assert second.id != row.id
    assert second.channel_id == row.channel_id


@pytest.mark.parametrize('trainer', [None, 999, 200])
async def test_no_trainer_or_no_party_uses_starter_range(battle_db, trainer):
    rng = BoundRandom()
    assert await EncounterV70Service(battle_db, rng=rng).spawn_level(trainer) == 3
    assert rng.bounds == (3, 7)


async def test_party_order_not_pokemon_id_selects_leader(battle_db):
    slots = (await battle_db.execute(select(PartySlot).where(PartySlot.owner_id == 1))).scalars().all()
    # Move the first Pokémon behind the second without violating slot uniqueness.
    slots.sort(key=lambda s: s.slot_index)
    slots[0].slot_index = 3
    (await battle_db.get(PokemonInstance, 2)).level = 40
    await battle_db.commit()
    rng = BoundRandom()
    assert await EncounterV70Service(battle_db, rng=rng).spawn_level(100) == 38
    assert rng.bounds == (38,42)


async def test_manual_and_automatic_spawns_pass_the_triggering_trainer():
    from cogs.encounters import EncounterCog
    from config import settings
    cog = object.__new__(EncounterCog)
    cog.activity = defaultdict(int)
    cog._spawn = AsyncMock()
    channel = SimpleNamespace(id=321)
    message = SimpleNamespace(author=SimpleNamespace(id=123, bot=False), channel=channel, guild=object())
    cog.activity[channel.id] = settings.spawn_message_threshold - 1
    await cog.on_message(message)
    cog._spawn.assert_awaited_once_with(channel, 123)
    cog._spawn.reset_mock()
    interaction = SimpleNamespace(channel=channel, channel_id=channel.id, user=SimpleNamespace(id=456))
    with patch('cogs.encounters.gui_defer', new=AsyncMock()), patch('cogs.encounters.gui_send', new=AsyncMock()):
        await EncounterCog.spawn.callback(cog, interaction)
    cog._spawn.assert_awaited_once_with(channel, 456)
