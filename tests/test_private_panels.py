import asyncio
from unittest.mock import AsyncMock

import discord
import pytest

from core.game_gui import OwnedView, gui_send, gui_defer
from core.private_panels import PANELS, key_for
from core.choice_buttons import choose
from gui_fakes import interaction, message


async def test_slash_commands_are_private_and_reuse_existing_panel():
    first = interaction()
    original = await gui_send(first, 'PC', ephemeral=False)
    assert first.response.send_message.call_args.kwargs['ephemeral'] is True
    second = interaction()
    reused = await gui_send(second, 'Shop')
    assert reused is original
    original.edit.assert_awaited_once()
    second.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)
    second.delete_original_response.assert_not_awaited()
    second.followup.send.assert_not_awaited()
    second.response.send_message.assert_not_awaited()


async def test_reused_panel_stays_visible_after_new_menu_slash_command():
    first = interaction()
    original = await gui_send(first, 'Trainer setup')
    menu = interaction()
    reused = await gui_send(menu, 'PokeBot • Adventure Hub')
    assert reused is original
    original.edit.assert_awaited_once()
    menu.response.defer.assert_awaited_once_with(ephemeral=True, thinking=True)
    menu.delete_original_response.assert_not_awaited()
    assert PANELS[key_for(menu)].message is original


async def test_multiple_results_do_not_delete_the_panel():
    click = interaction()
    original = await gui_send(click, 'First')
    await gui_send(click, 'Second')
    click.edit_original_response.assert_awaited_once()
    click.delete_original_response.assert_not_awaited()
    assert PANELS[key_for(click)].message is original


async def test_buttons_and_deferred_actions_edit_private_source():
    source = message()
    click = interaction(source=source)
    await gui_send(click, 'Choices')
    click.response.edit_message.assert_awaited_once()
    assert PANELS[key_for(click)].message is source
    deferred = interaction(source=source)
    await gui_defer(deferred, ephemeral=True, thinking=True)
    await gui_send(deferred, 'Purchased')
    deferred.response.defer.assert_awaited_once_with(thinking=False)
    source.edit.assert_awaited_once()
    deferred.edit_original_response.assert_not_awaited()
    deferred.followup.send.assert_not_awaited()


async def test_players_and_channels_have_separate_panels():
    for player, channel in [(1,10),(2,10),(1,11)]:
        await gui_send(interaction(user_id=player, channel_id=channel), 'Private')
    assert len(PANELS) == 3
    assert len({panel.message.id for panel in PANELS.values()}) == 3


async def test_public_and_other_players_messages_are_never_overwritten():
    for source in (message(ephemeral=False), message(owner=2)):
        click = interaction(source=source)
        await gui_send(click, 'My balance')
        source.edit.assert_not_awaited()
        click.response.edit_message.assert_not_awaited()
        click.edit_original_response.assert_not_awaited()
        PANELS.clear()


async def test_expired_panel_gets_one_private_replacement():
    first = interaction()
    panel = await gui_send(first, 'Old')
    panel.edit.side_effect = discord.NotFound(type('Response', (), {'status':404, 'reason':'Not Found'})(), 'Unknown webhook')
    click = interaction()
    new = await gui_send(click, 'New')
    assert new.id != panel.id
    click.edit_original_response.assert_awaited_once()
    click.followup.send.assert_not_awaited()
    click.delete_original_response.assert_not_awaited()


async def test_old_view_timeout_cannot_disable_replacement():
    first = interaction()
    old = OwnedView(1)
    original = await gui_send(first, 'Old menu', view=old)
    newer = OwnedView(1)
    await gui_send(interaction(source=original), 'New menu', view=newer)
    assert old.is_finished() and old.message is None
    await old.on_timeout()
    original.edit.assert_not_awaited()
    assert newer.message is original and not newer.is_finished()


async def test_concurrent_open_commands_create_only_one_panel():
    clicks = [interaction(), interaction()]
    results = await asyncio.gather(*(gui_send(click, 'Menu') for click in clicks))
    assert results[0].id == results[1].id
    assert sum(click.response.send_message.await_count for click in clicks) == 1


async def test_choice_to_receipt_uses_one_message_and_is_single_use():
    first = interaction()
    async def purchase(click, value):
        await gui_send(click, 'Gold remaining: 500')
    action = AsyncMock(side_effect=purchase)
    await choose(first, 'Heal?', [('Heal party',True)], action)
    panel = PANELS[key_for(first)]
    button = panel.view.children[0]
    clicks = [interaction(source=panel.message), interaction(source=panel.message)]
    await asyncio.gather(*(button.callback(click) for click in clicks))
    action.assert_awaited_once()
    assert sum(click.edit_original_response.await_count for click in clicks) == 1
    for click in clicks:
        click.followup.send.assert_not_awaited()
        click.response.send_message.assert_not_awaited()


async def test_public_spawn_button_opens_private_panel_without_changing_invitation():
    from datetime import datetime, timedelta
    from types import SimpleNamespace
    from core.wild_battle_view import SpawnLobbyView
    source = message(ephemeral=False)
    row = SimpleNamespace(id=42, expires_at=datetime.utcnow()+timedelta(minutes=5))
    async def open_encounter(click, encounter_id):
        assert encounter_id == 42
        await gui_send(click, 'Private encounter controls')
    view = SpawnLobbyView(row, open_encounter)
    click = interaction(user_id=2, source=source)
    await view.children[0].callback(click)
    click.response.defer.assert_not_awaited()
    click.response.send_message.assert_awaited_once()
    assert click.response.send_message.call_args.kwargs['ephemeral'] is True
    source.edit.assert_not_awaited()
    assert PANELS[key_for(click)].message.id != source.id


async def test_acknowledged_public_button_never_deletes_public_message():
    await gui_send(interaction(), 'Existing private menu')
    source = message(ephemeral=False)
    click = interaction(source=source, done=True)
    await gui_send(click, 'Private result')
    click.delete_original_response.assert_not_awaited()
    source.edit.assert_not_awaited()


async def test_private_modal_submission_reuses_panel():
    first = interaction()
    original = await gui_send(first, 'Custom input')
    # Modal submissions can arrive without a source message.
    submit = interaction(done=True)
    await gui_send(submit, 'Selection saved')
    assert PANELS[key_for(submit)].message is original
    original.edit.assert_awaited_once()
    submit.followup.send.assert_not_awaited()


async def test_wild_battle_view_rejects_another_players_controls():
    from datetime import datetime, timedelta
    from types import SimpleNamespace
    from core.wild_battle_view import WildBattleView
    row = SimpleNamespace(id=1, status='open', battle_state_json='{}', expires_at=datetime.utcnow()+timedelta(minutes=5))
    action = AsyncMock()
    view = WildBattleView(row, action, owner_id=1)
    foreign = interaction(user_id=2, source=message(owner=1))
    assert not await view.interaction_check(foreign)
    action.assert_not_awaited()
    foreign.response.edit_message.assert_not_awaited()
    assert PANELS[key_for(foreign)].message.interaction_metadata.user.id == 2


async def test_encounter_loader_does_not_show_another_trainers_battle_data():
    import json
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch
    from cogs.encounters import EncounterCog
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    row = SimpleNamespace(id=42, battle_state_json=json.dumps({'owner':1, 'gold_balance':987654}))
    click = interaction(user_id=2)
    cog = object.__new__(EncounterCog)
    with patch('cogs.encounters.SessionLocal', return_value=session), patch('cogs.encounters.WildEncounterRepository') as repo:
        repo.return_value.get_active = AsyncMock(return_value=row)
        await cog.open_encounter(click, 42)
    embed = click.response.send_message.call_args.kwargs['embeds'][0]
    assert '987654' not in embed.description
    assert click.response.send_message.call_args.kwargs['ephemeral'] is True

