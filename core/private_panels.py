"""One private GUI message per player/channel, refreshed through interaction tokens."""
import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from time import monotonic
from weakref import WeakValueDictionary

import discord


@dataclass
class Panel:
    message: object
    view: object
    touched: float


PANELS = OrderedDict()
LOCKS = WeakValueDictionary()
MAX_PANELS = 2048
TOKEN_LIFETIME = 14 * 60


def key_for(interaction):
    return (getattr(interaction, 'guild_id', None), getattr(interaction, 'channel_id', None), interaction.user.id)


def private_source(interaction):
    """Never edit a public message or another player's panel with private results."""
    message = getattr(interaction, 'message', None)
    if message is None or getattr(getattr(message, 'flags', None), 'ephemeral', False) is not True:
        return False
    metadata = getattr(message, 'interaction_metadata', None) or getattr(message, 'interaction', None)
    owner = getattr(getattr(metadata, 'user', None), 'id', None)
    if owner is not None:
        return owner == interaction.user.id
    panel = PANELS.get(key_for(interaction))
    return panel is not None and panel.message.id == message.id


async def defer(interaction):
    if not interaction.response.is_done():
        if private_source(interaction):
            await interaction.response.defer(thinking=False)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)


def remember(key, message, view, *, touched=None):
    previous = PANELS.pop(key, None)
    if previous is not None and previous.view is not view:
        if previous.view is not None:
            previous.view.stop()
            previous.view.message = None  # A previous screen's timeout must not erase the new screen.
    if view is not None:
        view.message = message
    PANELS[key] = Panel(message, view, monotonic() if touched is None else touched)
    while len(PANELS) > MAX_PANELS:
        _, expired = PANELS.popitem(last=False)
        if expired.view is not None:
            expired.view.stop()
            expired.view.message = None


async def deliver(interaction, content=None, **kwargs):
    # GUI responses are always private, regardless of an older command's flag.
    kwargs.pop('ephemeral', None)
    kwargs.pop('wait', None)
    kwargs.setdefault('allowed_mentions', discord.AllowedMentions.none())
    kwargs.setdefault('attachments', [])
    if 'embed' in kwargs:
        kwargs['embeds'] = [kwargs.pop('embed')]
    kwargs.setdefault('embeds', [])
    key = key_for(interaction)
    extras = getattr(interaction, 'extras', None)
    if extras is None:
        extras = {}
        interaction.extras = extras
    lock = LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        LOCKS[key] = lock
    async with lock:
        source = private_source(interaction) or extras.get('gui_original_is_panel', False)
        if source:
            if interaction.response.is_done():
                message = await interaction.edit_original_response(content=content, **kwargs)
            else:
                await interaction.response.edit_message(content=content, **kwargs)
                message = await interaction.original_response()
            remember(key, message, kwargs.get('view'))
            extras['gui_original_is_panel'] = True
            return message

        panel = PANELS.get(key)
        if panel is not None and monotonic() - panel.touched < TOKEN_LIFETIME:
            await defer(interaction)
            try:
                message = await panel.message.edit(content=content, **kwargs)
            except discord.HTTPException as exc:
                # Expired/dismissed ephemeral message: replace it once, privately.
                if exc.status not in (401, 403, 404):
                    raise
            else:
                # Remove the new slash-command acknowledgement after reusing the old panel.
                if not extras.get('gui_ack_deleted') and getattr(interaction.response, 'type', None) != discord.InteractionResponseType.deferred_message_update:
                    try:
                        await interaction.delete_original_response()
                    except discord.NotFound:
                        pass
                    extras['gui_ack_deleted'] = True
                remember(key, message, kwargs.get('view'), touched=panel.touched)
                return message

        if interaction.response.is_done() and getattr(interaction.response, 'type', None) == discord.InteractionResponseType.deferred_message_update:
            send_kwargs = {k: v for k, v in kwargs.items() if k != 'attachments'}
            message = await interaction.followup.send(content=content, ephemeral=True, wait=True, **send_kwargs)
        elif interaction.response.is_done():
            message = await interaction.edit_original_response(content=content, **kwargs)
            extras['gui_original_is_panel'] = True
        else:
            send_kwargs = {k: v for k, v in kwargs.items() if k != 'attachments'}
            await interaction.response.send_message(content=content, ephemeral=True, **send_kwargs)
            message = await interaction.original_response()
            extras['gui_original_is_panel'] = True
        remember(key, message, kwargs.get('view'))
        return message
