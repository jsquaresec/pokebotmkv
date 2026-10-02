import json

import pytest
from sqlalchemy import delete

from models import User, PokemonInstance, PartySlot
from services.pokemon_center_service import PokemonCenterService
from test_wild_battles import battle_db


async def test_center_revives_whole_party_restores_pp_and_charges_once(battle_db):
    user = await battle_db.get(User, 1)
    user.balance = 1000
    for pid in (1, 2):
        mon = await battle_db.get(PokemonInstance, pid)
        mon.current_hp = 0 if pid == 1 else 30
        mon.moves_json = json.dumps([dict(name="Tackle", pp=0, max_pp=35)])
    await battle_db.commit()
    count, balance = await PokemonCenterService(battle_db).heal_party(100)
    await battle_db.commit()
    assert (count, balance) == (2, 500)
    for pid in (1, 2):
        mon = await battle_db.get(PokemonInstance, pid)
        await battle_db.refresh(mon)
        assert mon.current_hp == mon.max_hp
        assert json.loads(mon.moves_json)[0]['pp'] == 35
    with pytest.raises(ValueError, match="already has full"):
        await PokemonCenterService(battle_db).heal_party(100)
    assert user.balance == 500


@pytest.mark.parametrize('condition, message', [
    ('poor', 'You have'), ('locked', 'busy'), ('empty', 'empty'), ('healthy', 'full HP')])
async def test_center_rejections_do_not_charge_or_heal(battle_db, condition, message):
    user = await battle_db.get(User, 1)
    mon = await battle_db.get(PokemonInstance, 1)
    if condition != 'healthy':
        mon.current_hp = 1
    if condition == 'poor':
        user.balance = 499
    if condition == 'locked':
        mon.locked = True
    if condition == 'empty':
        await battle_db.execute(delete(PartySlot).where(PartySlot.owner_id == 1))
    await battle_db.commit()
    with pytest.raises(ValueError, match=message):
        await PokemonCenterService(battle_db).heal_party(100)
    assert user.balance == (499 if condition == 'poor' else 1000)
    assert mon.current_hp == (100 if condition == 'healthy' else 1)
