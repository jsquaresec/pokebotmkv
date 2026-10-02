"""Button-driven input collection for every command that takes arguments."""
import asyncio

import discord
from discord import app_commands

from core.game_gui import OwnedView, card, check_command, execute, gui_defer, gui_send, parse_value
from services.button_options import options_for


class ButtonFlow:
    def __init__(self, command, owner_id):
        self.command = command
        self.owner_id = owner_id
        self.parameters = command.parameters
        self.values = {}
        self.labels = {}
        self.index = 0
        self.page = 0
        self.version = 0
        self.closed = False
        self.message = None
        self.view = None
        self.lock = asyncio.Lock()

    async def show(self, interaction, error=None):
        await check_command(interaction, self.command, run_checks=False)
        if self.view:
            self.view.stop()
        self.version += 1
        options, custom = [], False
        if self.index < len(self.parameters):
            parameter = self.parameters[self.index]
            options, custom = await options_for(interaction, self.command, parameter, self.values)
            options = [(label, value, False) for label, value in options]
            if not parameter.required:
                label = "Skip / use default" if parameter.default is None else f"Default: {parameter.default}"
                options.insert(0, (label, parameter.default, True))
            heading = parameter.display_name.replace("_", " ").title()
            body = f"**Step {self.index + 1}/{len(self.parameters)}: {heading}**\nChoose a button below."
            if not options:
                body += "\nUse Custom to enter a value." if custom else "\nNo eligible choices are available. Go back or cancel."
            if len(options) > 20:
                body += f"\nPage {self.page + 1}/{(len(options) + 19) // 20}"
        else:
            body = "**Review your selection**\n" + "\n".join(
                f'**{p.display_name.replace("_", " ").title()}:** {self.labels[p.name]}' for p in self.parameters)
            body += "\n\nClick **Run Action** to apply these selections."
        if error:
            body = f"{error}\n\n" + body
        self.view = FlowView(self, options, custom)
        embed = card(self.command.name.replace("_", " ").title(), body[:4000])
        self.message = await gui_send(interaction, embed=embed, view=self.view, ephemeral=True)
        self.view.message = self.message

    async def select(self, interaction, value, label, default=False):
        parameter = self.parameters[self.index]
        try:
            result = value if default else await parse_value(interaction, parameter, str(value))
        except (ValueError, app_commands.AppCommandError) as exc:
            await self.show(interaction, str(exc))
            return
        self.values[parameter.name] = result
        self.labels[parameter.name] = label
        self.index += 1
        self.page = 0
        await self.show(interaction)


class FlowView(OwnedView):
    def __init__(self, flow, options, custom):
        super().__init__(flow.owner_id)
        self.flow, self.version = flow, flow.version
        for index, (label, value, default) in enumerate(options[flow.page * 20:(flow.page + 1) * 20]):
            async def select(interaction, choice=value, text=label, use_default=default):
                await self.apply(interaction, lambda: flow.select(interaction, choice, text, use_default))
            self.button(str(label), select, row=index // 5)
        for label, delta in (("Previous", -1), ("Next", 1)):
            if 0 <= flow.page + delta < (len(options) + 19) // 20:
                async def navigate(interaction, step=delta):
                    async def change():
                        flow.page += step
                        await flow.show(interaction)
                    await self.apply(interaction, change)
                self.button(label, navigate, row=4)
        if flow.index:
            async def back(interaction):
                async def change():
                    flow.index -= 1
                    for p in flow.parameters[flow.index:]:
                        flow.values.pop(p.name, None)
                        flow.labels.pop(p.name, None)
                    flow.page = 0
                    await flow.show(interaction)
                await self.apply(interaction, change)
            self.button("Back", back, row=4)
        async def cancel(interaction):
            async def close():
                flow.closed = True
                self.stop()
                await gui_send(interaction, "Nothing was applied. Choose Home to open another action.")
            await self.apply(interaction, close)
        self.button("Cancel", cancel, row=4)
        if custom:
            async def enter(interaction):
                async with flow.lock:
                    if flow.closed or flow.version != self.version or self.is_finished():
                        await interaction.response.defer(thinking=False)
                        return
                    await interaction.response.send_modal(CustomValue(flow, self.version))
            self.button("Custom…", enter, row=4, style=discord.ButtonStyle.primary)
        if flow.index == len(flow.parameters):
            async def run(interaction):
                async def perform():
                    flow.closed = True
                    self.stop()
                    for button in self.children:
                        button.disabled = True
                    await execute(interaction, flow.command, dict(flow.values))
                await self.apply(interaction, perform)
            self.button("Run Action", run, row=4, style=discord.ButtonStyle.success)

    async def apply(self, interaction, action):
        await gui_defer(interaction)
        async with self.flow.lock:
            if self.flow.closed or self.flow.version != self.version or self.is_finished():
                return
            await action()

    async def on_timeout(self):
        async with self.flow.lock:
            if self.flow.version == self.version:
                self.flow.closed = True
                await super().on_timeout()


class CustomValue(discord.ui.Modal):
    def __init__(self, flow, version):
        parameter = flow.parameters[flow.index]
        super().__init__(title=f'Custom {parameter.display_name}'[:45], timeout=300)
        self.flow, self.version = flow, version
        self.field = discord.ui.TextInput(label=parameter.display_name.replace("_", " ").title()[:45],
                                         required=True, max_length=1000)
        self.add_item(self.field)

    async def on_submit(self, interaction):
        await gui_defer(interaction)
        async with self.flow.lock:
            if interaction.user.id != self.flow.owner_id or self.flow.closed or self.flow.version != self.version:
                return
            await self.flow.select(interaction, self.field.value, self.field.value)

    async def on_error(self, interaction, error):
        await self.flow.view.on_error(interaction, error, self.field)


async def begin_flow(interaction, command):
    await gui_defer(interaction, ephemeral=True, thinking=True)
    flow = ButtonFlow(command, interaction.user.id)
    await flow.show(interaction)


def install_button_commands(bot):
    """Keep original bound handlers while publishing argument-free entrypoints."""
    for original in list(bot.tree.get_commands()):
        if not isinstance(original, app_commands.Command) or not original.parameters:
            continue

        def entrypoint(target):
            async def open_buttons(interaction: discord.Interaction):
                from core.game_gui import launch
                await launch(interaction, target)
            return open_buttons

        entry = app_commands.Command(
            name=original.name, description=original.description, callback=entrypoint(original),
            nsfw=original.nsfw,
            extras={**original.extras, "button_target": original},
        )
        entry.guild_only = original.guild_only
        entry.default_permissions = original.default_permissions
        entry.allowed_contexts = original.allowed_contexts
        entry.allowed_installs = original.allowed_installs
        bot.tree.remove_command(original.name)
        bot.tree.add_command(entry)
