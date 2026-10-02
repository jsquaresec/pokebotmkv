import asyncio

import discord

from core.game_gui import OwnedView, card, gui_send, gui_defer


class PartyBuilder(OwnedView):
    def __init__(self, owner_id, pokemon, selected, save):
        super().__init__(owner_id)
        self.pokemon = list(pokemon)
        self.by_id = {mon.id: mon for mon in self.pokemon}
        self.selected = [pid for pid in selected if pid in self.by_id][:6]
        self.save_action = save
        self.page = 0
        self.closed = False
        self.lock = asyncio.Lock()
        self.render()

    def embed(self, status=None):
        lines = [f'**{i}.** {self.by_id[pid].display_name} · Lv.{self.by_id[pid].level} · #{pid}'
                 for i, pid in enumerate(self.selected, 1)]
        body = (status or "Click Pokémon to add or remove them. Selection order sets party order; slot 1 leads.")
        body += "\n\n" + ("\n".join(lines) or "Your selection is empty.")
        body += f"\n\n**{len(self.selected)}/6 selected** · Page {self.page + 1}/{max(1, (len(self.pokemon) + 19) // 20)}"
        if not self.closed:
            body += "\nChanges take effect only when you click **Save Party**."
        return card("Build your party", body)

    def render(self):
        self.clear_items()
        for index, mon in enumerate(self.pokemon[self.page * 20:(self.page + 1) * 20]):
            selected = mon.id in self.selected

            async def toggle(interaction, pid=mon.id):
                async with self.lock:
                    if self.closed or self.is_finished():
                        await gui_defer(interaction)
                        return
                    if pid in self.selected:
                        self.selected.remove(pid)
                    elif len(self.selected) < 6:
                        self.selected.append(pid)
                    self.render()
                    await interaction.response.edit_message(embed=self.embed(), view=self)

            self.button(f'{"✓ " if selected else ""}{mon.display_name} · Lv.{mon.level} · #{mon.id}', toggle,
                        row=index // 5, style=discord.ButtonStyle.success if selected else discord.ButtonStyle.secondary,
                        disabled=self.closed or (len(self.selected) == 6 and not selected))
        for label, step in (("Previous", -1), ("Next", 1)):
            async def navigate(interaction, delta=step):
                async with self.lock:
                    if self.closed or self.is_finished():
                        await gui_defer(interaction)
                        return
                    self.page = max(0, min(self.page + delta, max(0, (len(self.pokemon) - 1) // 20)))
                    self.render()
                    await interaction.response.edit_message(embed=self.embed(), view=self)
            self.button(label, navigate, row=4,
                        disabled=self.closed or not 0 <= self.page + step < (len(self.pokemon) + 19) // 20)
        self.button("Clear Selection", self.clear, row=4, disabled=self.closed)
        self.button("Cancel", self.cancel, row=4, disabled=self.closed)
        self.button("Save Party", self.save, row=4, style=discord.ButtonStyle.primary, disabled=self.closed)

    async def clear(self, interaction):
        async with self.lock:
            if self.is_finished():
                await gui_defer(interaction)
                return
            if not self.closed:
                self.selected.clear()
                self.render()
            await interaction.response.edit_message(embed=self.embed(), view=self)

    async def cancel(self, interaction):
        async with self.lock:
            if self.is_finished():
                await gui_defer(interaction)
                return
            self.closed = True
            self.render()
            self.stop()
            await interaction.response.edit_message(embed=self.embed("Cancelled. Your saved party was not changed."), view=self)

    async def save(self, interaction):
        await gui_defer(interaction)
        async with self.lock:
            if self.closed or self.is_finished():
                return
            if not await self.save_action(interaction, list(self.selected)):
                return
            self.closed = True
            self.render()
            self.stop()
            # The save action already replaced this panel with its receipt and Home button.

    async def on_timeout(self):
        async with self.lock:
            self.closed = True
            await super().on_timeout()
