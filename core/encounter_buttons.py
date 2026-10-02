import asyncio
import logging

import discord

from services.encounter_ui import encounter_card, caught_card


class EncounterButtons(discord.ui.View):
    """Shared encounter controls: every player uses their own inventory."""

    def __init__(self, encounter_id, attack, catch, timeout, encounter=None):
        super().__init__(timeout=max(1, timeout))
        self.encounter_id = encounter_id
        self.lock = asyncio.Lock()
        self.closed = False
        self.message = None
        self.encounter = encounter
        for label, ball in [("Weaken", None), ("Poké Ball", "poke_ball"),
                            ("Great Ball", "great_ball"), ("Ultra Ball", "ultra_ball"),
                            ("Master Ball", "master_ball")]:
            emoji = {None: "⚔️", "poke_ball": "🔴", "great_ball": "🔵", "ultra_ball": "🟡", "master_ball": "🟣"}[ball]
            button = discord.ui.Button(label=label, emoji=emoji, row=0 if ball is None else 1,
                                       style=(discord.ButtonStyle.success if ball else discord.ButtonStyle.primary))

            async def act(interaction, selected=ball):
                await interaction.response.defer(thinking=False)
                async with self.lock:
                    if self.closed:
                        return
                    try:
                        if selected is None:
                            row = await attack(interaction, self.encounter_id, notify=False)
                            if row:
                                self.encounter = row
                                await self.status(interaction, "The Pokémon was weakened. Catch odds updated.")
                        else:
                            mon = await catch(interaction, selected, self.encounter_id, notify=False)
                            if mon:
                                self.disable()
                                self.stop()
                                await interaction.message.edit(
                                    content=None, embed=caught_card(mon, interaction.user.id), view=self)
                            else:
                                await self.status(interaction, "The Pokémon broke free! Weaken it or try another ball.")
                    except ValueError as exc:
                        await self.status(interaction, str(exc))

            button.callback = act
            self.add_item(button)

    async def status(self, interaction, text):
        embed = encounter_card(self.encounter) if self.encounter else discord.Embed(title="Wild encounter")
        embed.add_field(name="Last action", value=text, inline=False)
        await interaction.message.edit(content=None, embed=embed, view=self)

    def disable(self):
        self.closed = True
        for child in self.children:
            child.disabled = True

    async def on_timeout(self):
        async with self.lock:
            self.disable()
            if self.message:
                try:
                    if self.encounter:
                        await self.message.edit(content=None, embed=encounter_card(self.encounter, expired=True), view=self)
                    else:
                        await self.message.edit(view=self)
                except discord.HTTPException:
                    pass

    async def on_error(self, interaction, error, item):
        logging.getLogger(__name__).error("Encounter button failed", exc_info=(type(error), error, error.__traceback__))
        if not interaction.response.is_done():
            await interaction.response.defer(thinking=False)
        try:
            await self.status(interaction, "The action could not be completed. Try again or reopen /encounter.")
        except discord.HTTPException:
            pass
