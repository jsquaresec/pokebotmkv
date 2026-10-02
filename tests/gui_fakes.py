"""Interaction fakes that model Discord acknowledgement and private-message edits."""
from itertools import count
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord

IDS = count(1000)


def message(owner=1, ephemeral=True, message_id=None):
    result = SimpleNamespace(id=message_id or next(IDS), flags=SimpleNamespace(ephemeral=ephemeral),
        interaction_metadata=SimpleNamespace(user=SimpleNamespace(id=owner)))
    result.edit = AsyncMock(return_value=result)
    return result


def interaction(user_id=1, done=False, source=None, admin=False, commands=(), channel_id=10, guild_id=20):
    response = SimpleNamespace(type=None)
    state = dict(done=done, original=source or message(user_id))
    if done:
        response.type = discord.InteractionResponseType.deferred_message_update if source else discord.InteractionResponseType.deferred_channel_message

    async def defer(**kwargs):
        state['done'] = True
        if kwargs.get('thinking') or source is None:
            response.type = discord.InteractionResponseType.deferred_channel_message
            state['original'] = message(user_id)
        else:
            response.type = discord.InteractionResponseType.deferred_message_update
    async def send(*args, **kwargs):
        state['done'] = True
        response.type = discord.InteractionResponseType.channel_message
        state['original'] = message(user_id, kwargs.get('ephemeral', False))
    async def edit(*args, **kwargs):
        state['done'] = True
        response.type = discord.InteractionResponseType.message_update
    async def original():
        return state['original']
    async def edit_original(*args, **kwargs):
        return state['original']
    response.is_done = Mock(side_effect=lambda: state['done'])
    response.defer = AsyncMock(side_effect=defer)
    response.send_message = AsyncMock(side_effect=send)
    response.edit_message = AsyncMock(side_effect=edit)
    response.send_modal = AsyncMock()
    return SimpleNamespace(user=SimpleNamespace(id=user_id), guild=object(), guild_id=guild_id,
        channel_id=channel_id, command=None, message=source, extras={},
        permissions=discord.Permissions(administrator=admin),
        client=SimpleNamespace(tree=SimpleNamespace(walk_commands=lambda: iter(commands), interaction_check=AsyncMock(return_value=True))),
        response=response, followup=SimpleNamespace(send=AsyncMock(return_value=message(user_id))),
        original_response=AsyncMock(side_effect=original), edit_original_response=AsyncMock(side_effect=edit_original),
        delete_original_response=AsyncMock())
