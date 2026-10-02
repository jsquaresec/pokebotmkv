import asyncio
import logging
from datetime import datetime

import discord

from services.encounter_ui import encounter_card, registry
from services.wild_battle_service import load_battle
from core.game_gui import OwnedView, ResultView, dashboard, gui_defer, gui_send


def battle_card(row, notice=None, owner_id=None):
    state = load_battle(row, owner_id)
    if state:
        row.status_effect = state["wild"].get("status")
    ended = row.status != "open" or bool(state.get("finished")) or row.expires_at <= datetime.utcnow()
    embed = encounter_card(row, expired=ended)
    if not state and not ended:
        embed.set_field_at(2, name="Wild battle", value="Click **Battle** to send out your party leader, then choose moves or throw a ball.", inline=False)
    elif state:
        active = state["team"][state["active"]]
        if ended:
            embed.title = {"caught": f'{row.species} caught! +500 gold', "won": "Wild battle won!",
                           "lost": "Your party fainted", "ran": "Escaped safely",
                           "expired": "Encounter expired"}.get(state.get("result"), "Encounter ended")
            embed.remove_field(1)  # Replace the generic expired-controls message.
            if state.get('result') == 'won' and state.get('gold_reward'):
                embed.add_field(name="Battle reward", value=f'**+{state["gold_reward"]:,} gold**', inline=False)
                embed.add_field(name="Gold remaining", value=f'**{state["gold_balance"]:,} gold**')
        embed.add_field(name=f'Your Pokémon · {active["name"]} Lv.{active["level"]}',
                        value=f'**{active["hp"]}/{active["max_hp"]} HP** · {active.get("status") or "Healthy"}', inline=False)
        embed.add_field(name="Trainer", value=f'<@{state["owner"]}> · Turn {state["turn"]}')
        if state["wild"].get("status"):
            embed.add_field(name="Wild status", value=state["wild"]["status"].title())
        if state.get("log"):
            embed.add_field(name="Battle log", value="\n".join(state["log"][-7:])[:1024], inline=False)
        if not ended:
            embed.set_field_at(2, name="Choose your turn", value="Use a move, throw a ball, switch Pokémon, or run. Fainted wild Pokémon cannot be caught.", inline=False)
    if notice:
        embed.add_field(name="Notice", value=notice[:1024], inline=False)
    embed.set_footer(text="Battle finished • Click Home to return to your private menu" if ended else
                     "Moves consume PP • HP and PP persist after battle • Use /encounter to resume")
    return embed


class WildBattleView(OwnedView):
    def __init__(self, row, action, owner_id=None):
        super().__init__(owner_id if owner_id is not None else load_battle(row).get('owner'))
        self.timeout = max(1, (row.expires_at - datetime.utcnow()).total_seconds())
        self.row, self.action = row, action
        self.lock = asyncio.Lock()
        self.message = None
        self.render()

    def render(self):
        self.clear_items()
        state = load_battle(self.row, self.owner_id)
        ended = self.row.status != "open" or bool(state.get("finished")) or self.row.expires_at <= datetime.utcnow()
        turn = state.get("turn", 0)
        if ended:
            self.timeout = 300
            self.button("Home", dashboard, emoji="🏠", style=discord.ButtonStyle.primary)
            return

        def add(label, kind, value=None, row=0, disabled=False, style=discord.ButtonStyle.secondary):
            button = discord.ui.Button(label=label[:80], row=row, disabled=disabled or ended, style=style)

            async def callback(interaction):
                async with self.lock:
                    if self.is_finished():
                        return
                    try:
                        self.row = await self.action(interaction, self.row.id, kind, value, turn)
                        self.render()
                        await gui_send(interaction, embed=battle_card(self.row, owner_id=self.owner_id), view=self)
                    except ValueError as exc:
                        await gui_send(interaction, embed=battle_card(self.row, str(exc), self.owner_id), view=self)
            button.callback = callback
            self.add_item(button)

        if not state:
            add("⚔️ Battle", "start", style=discord.ButtonStyle.primary)
            self.button("Home", dashboard, row=3)
            return
        active = state["team"][state["active"]]
        moves = active["moves"]
        has_pp = any(slot["pp"] > 0 and (registry().move(slot['name']) or {}).get('battle_supported', False) for slot in moves)
        for slot in moves[:4]:
            data = registry().move(slot["name"]) or {}
            add(f'{slot["name"]} · {data.get("type", "normal").title()} · {slot["pp"]}/{slot["max_pp"]} PP', "move", slot["name"],
                disabled=slot["pp"] <= 0 or active["hp"] <= 0 or not data.get('battle_supported', False), style=discord.ButtonStyle.primary)
        if not has_pp:
            add("Struggle", "move", "Struggle", disabled=active["hp"] <= 0, style=discord.ButtonStyle.danger)
        for label, ball in (("🔴 Poké Ball", "poke_ball"), ("🔵 Great Ball", "great_ball"),
                            ("🟡 Ultra Ball", "ultra_ball"), ("🟣 Master Ball", "master_ball")):
            add(label, "ball", ball, row=1, disabled=active["hp"] <= 0, style=discord.ButtonStyle.success)
        bench = [(i, mon) for i, mon in enumerate(state["team"]) if i != state["active"]]
        for index, mon in bench:
            add(f'Switch: {mon["name"]} · {mon["hp"]} HP', "switch", index, row=2, disabled=mon["hp"] <= 0)
        add("Run", "run", row=3, style=discord.ButtonStyle.danger)
        self.button("Home", dashboard, row=3)

    async def on_timeout(self):
        if self.row.status != 'open' or load_battle(self.row, self.owner_id).get('finished'):
            await super().on_timeout()
            return
        if self.message:
            try:
                home = ResultView(self.owner_id)
                message = await self.message.edit(embed=battle_card(self.row, "Encounter expired. Click Home to return to your menu.", self.owner_id), view=home)
                home.message = message
                from core.private_panels import PANELS, remember
                for key, panel in list(PANELS.items()):
                    if panel.view is self:
                        remember(key, message, home, touched=panel.touched)
            except discord.HTTPException:
                pass

    async def on_error(self, interaction, error, item):
        logging.getLogger(__name__).error("Wild battle action failed", exc_info=(type(error), error, error.__traceback__))
        await gui_defer(interaction)
        try:
            await gui_send(interaction, embed=battle_card(self.row, "The turn failed. Reopen /encounter to refresh.", self.owner_id), view=self)
        except discord.HTTPException:
            pass


class SpawnLobbyView(discord.ui.View):
    """Public discovery button; all trainer controls open in a private panel."""
    def __init__(self, row, open_encounter):
        super().__init__(timeout=max(1, (row.expires_at - datetime.utcnow()).total_seconds()))
        self.message = None
        button = discord.ui.Button(label="Open private encounter", style=discord.ButtonStyle.primary)

        async def open_private(interaction):
            # The public spawn is discovery only. Never edit it and never reuse
            # an unrelated trainer menu: create a dedicated ephemeral battle GUI.
            interaction.extras["gui_force_private_panel"] = True
            await open_encounter(interaction, row.id)

        button.callback = open_private
        self.add_item(button)

    async def on_timeout(self):
        for button in self.children:
            button.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def on_error(self, interaction, error, item):
        logging.getLogger(__name__).error("Could not open private encounter", exc_info=(type(error), error, error.__traceback__))
        await gui_send(interaction, "Could not open the encounter. Try /encounter again.")
