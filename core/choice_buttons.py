"""Private, paginated, single-use choice menus shared by bot commands."""
import asyncio
import logging

import discord
from core.game_gui import OwnedView, gui_send, gui_defer


async def reply(interaction, content, **kwargs):
    return await gui_send(interaction, content, **kwargs)


class ChoiceButtons(OwnedView):
    def __init__(self, owner_id, options, callback):
        super().__init__(owner_id)
        self.timeout = 180
        self.options = list(options)
        self.action = callback
        self.page = 0
        self.used = False
        self.lock = asyncio.Lock()
        self.message = None
        self.render()

    def render(self):
        self.clear_items()
        for index, (label, value) in enumerate(self.options[self.page * 20:(self.page + 1) * 20]):
            button = discord.ui.Button(label=str(label)[:80], row=index // 5)

            async def select(interaction, selected=value):
                async with self.lock:
                    if self.used or self.is_finished():
                        # A duplicate click must be acknowledged, but it cannot
                        # execute this single-use action.
                        if not interaction.response.is_done():
                            await interaction.response.defer(thinking=False)
                        return
                    self.used = True
                    for child in self.children:
                        child.disabled = True
                    self.stop()
                    await self.action(interaction, selected)

            button.callback = select
            self.add_item(button)
        if len(self.options) > 20:
            for label, delta in (("Previous", -1), ("Next", 1)):
                button = discord.ui.Button(label=label, row=4)
                button.disabled = not 0 <= self.page + delta <= (len(self.options) - 1) // 20

                async def navigate(interaction, step=delta):
                    async with self.lock:
                        if self.used or self.is_finished():
                            await gui_defer(interaction)
                            return
                        self.page = max(0, min(self.page + step, (len(self.options) - 1) // 20))
                        self.render()
                        await interaction.response.edit_message(view=self)

                button.callback = navigate
                self.add_item(button)

    async def interaction_check(self, interaction):
        return await super().interaction_check(interaction)

    async def on_timeout(self):
        self.used = True
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content="Menu expired. Run the command again.", view=self)
            except discord.HTTPException:
                pass

    async def on_error(self, interaction, error, item):
        logging.getLogger(__name__).error("Button action failed", exc_info=(type(error), error, error.__traceback__))
        await reply(interaction, "That action failed. Please reopen the menu and try again.", ephemeral=True)


async def choose(interaction, prompt, options, callback):
    options = list(options)
    if not options:
        await reply(interaction, "No available options right now.", ephemeral=True)
        return
    view = ChoiceButtons(interaction.user.id, options, callback)
    view.message = await gui_send(interaction, prompt, view=view, ephemeral=True)
