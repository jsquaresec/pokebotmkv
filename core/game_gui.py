"""Discord dashboard, command forms, and result cards for the whole bot."""
import logging
import math
from contextvars import ContextVar

import discord
from discord import app_commands
from core.private_panels import deliver, defer

_ACTIVE_COMMAND = ContextVar("gui_command", default=None)


CATEGORIES = {
    "Trainer": ("profile", "trainer_v80", "cosmetics"),
    "Pokémon & Party": ("pokemon", "party"),
    "Catching": ("encounters", "catch"),
    "Shop & Trading": ("economy", "market", "auctions"),
    "Battles & Ranked": ("battle", "ranked", "replay"),
    "Daily & Seasons": ("retention", "season_pass"),
    "Friends & Guilds": ("social", "guild"),
    "World & Events": ("regions", "content", "events", "live_events"),
    "Help & Status": ("onboarding", "system_v80"),
    "Admin & Previews": ("admin", "admin_debug", "admin_playtest", "ui_preview", "balance_preview"),
}


def category_for(command):
    command = command.extras.get("button_target", command)
    module = command.callback.__module__.rsplit(".", 1)[-1]
    return next((name for name, modules in CATEGORIES.items() if module in modules), "Help & Status")


def card(title, body):
    embed = discord.Embed(title=title[:256], description=body, color=0x5865F2)
    embed.set_footer(text="PokeBot • Your adventure, one click away")
    return embed


def command_title(interaction):
    command = _ACTIVE_COMMAND.get() or getattr(interaction, "command", None)
    return command.name.replace("_", " ").title() if command else "PokeBot"


class OwnedView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.message = None

    async def interaction_check(self, interaction):
        if interaction.user.id == self.owner_id and not self.is_finished():
            return True
        if interaction.user.id != self.owner_id:
            await gui_send(interaction, "Open /menu to use your own dashboard.", ephemeral=True)
        else:
            await gui_defer(interaction)
        return False

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def on_error(self, interaction, error, item):
        logging.getLogger(__name__).error("GUI action failed", exc_info=(type(error), error, error.__traceback__))
        await gui_send(interaction, "This action failed. Open /menu and try again.", ephemeral=True)

    def button(self, label, callback, **kwargs):
        button = discord.ui.Button(label=label[:80], **kwargs)
        button.callback = callback
        self.add_item(button)


class ResultView(OwnedView):
    def __init__(self, owner_id, pages=None, title="PokeBot"):
        super().__init__(owner_id)
        self.pages = pages or []
        self.title = title
        self.page = 0
        self.render()

    def render(self):
        self.clear_items()
        self.button("Home", lambda i: dashboard(i), style=discord.ButtonStyle.primary, emoji="🏠")
        if len(self.pages) > 1:
            for label, step in (("Previous", -1), ("Next", 1)):
                async def turn(interaction, delta=step):
                    if self.is_finished():
                        await gui_defer(interaction)
                        return
                    self.page = max(0, min(self.page + delta, len(self.pages) - 1))
                    self.render()
                    await interaction.response.edit_message(embed=self.embed(), view=self)
                self.button(label, turn, disabled=not 0 <= self.page + step < len(self.pages))

    def embed(self):
        embed = card(self.title, self.pages[self.page])
        embed.set_footer(text=f"PokeBot • Page {self.page + 1}/{len(self.pages)}")
        return embed


async def gui_send(interaction, content=None, **kwargs):
    """Preserve custom cards/buttons; give plain responses a card and navigation."""
    if content is not None and not kwargs.get("embed") and not kwargs.get("embeds"):
        text = str(content)
        pages = [text[i:i + 3800] for i in range(0, len(text), 3800)] or ["Nothing to show yet."]
        if len(pages) > 1 and kwargs.get("view") is None:
            view = ResultView(interaction.user.id, pages, command_title(interaction))
            kwargs["view"], kwargs["embed"] = view, view.embed()
        else:
            kwargs["embed"] = card(command_title(interaction), pages[0])
        content = None
    if kwargs.get("view") is None:
        kwargs["view"] = ResultView(interaction.user.id)
    return await deliver(interaction, content, **kwargs)


async def gui_defer(interaction, **kwargs):
    await defer(interaction)


def available_commands(interaction):
    return [command for command in interaction.client.tree.walk_commands()
            if isinstance(command, app_commands.Command) and command.name != "menu"
            and (category_for(command) != "Admin & Previews" or interaction.permissions.administrator)
            and (not command.guild_only or interaction.guild is not None)]


class DashboardView(OwnedView):
    def __init__(self, interaction, category=None, page=0):
        super().__init__(interaction.user.id)
        commands = available_commands(interaction)
        if category is None:
            present = {category_for(command) for command in commands}
            for name in CATEGORIES:
                if name in present:
                    async def open_category(click, selected=name):
                        await dashboard(click, selected)
                    self.button(name, open_category, style=discord.ButtonStyle.primary)
        else:
            commands = sorted((c for c in commands if category_for(c) == category), key=lambda c: c.name)
            for command in commands[page * 20:(page + 1) * 20]:
                async def open_command(click, selected=command):
                    await launch(click, selected)
                self.button(command.name.replace("_", " ").title(), open_command)
            self.button("Home", lambda i: dashboard(i), row=4, style=discord.ButtonStyle.primary)
            for label, delta in (("Previous", -1), ("Next", 1)):
                if 0 <= page + delta < math.ceil(len(commands) / 20):
                    async def turn(click, destination=page + delta):
                        await dashboard(click, category, destination)
                    self.button(label, turn, row=4)


async def dashboard(interaction, category=None, page=0):
    commands = available_commands(interaction)
    if category:
        commands = sorted((c for c in commands if category_for(c) == category), key=lambda c: c.name)
        body = "\n".join(f'**{c.name.replace("_", " ").title()}** — {c.description}'
                         for c in commands[page * 20:(page + 1) * 20])
    else:
        body = ("**Welcome, Trainer!**\nChoose a section below to explore, manage your Pokémon, or play.\n\n"
                "👤 **Trainer** · Profile, starters, achievements\n"
                "🎒 **Pokémon & Party** · Collection and team\n"
                "🛒 **Shop & Trading** · Items, market, auctions\n"
                "⚔️ **Battles & Ranked** · Moves and matchmaking\n"
                "🌍 **World & Friends** · Events, regions, guilds\n\n"
                "Buttons open screens and forms. No command names to remember.")
    await gui_send(interaction, embed=card(category or "PokeBot • Adventure Hub", body or "No actions available."),
                   view=DashboardView(interaction, category, page), ephemeral=True)


async def check_command(interaction, command, run_checks=True):
    if command.guild_only and interaction.guild is None:
        raise ValueError("Open this action inside a server.")
    if category_for(command) == "Admin & Previews" and not interaction.permissions.administrator:
        raise ValueError("Administrator permission is required for this screen.")
    required = command.default_permissions
    if required is not None and not interaction.permissions.administrator:
        if required.value == 0 or (interaction.permissions.value & required.value) != required.value:
            raise ValueError("You do not have the server permissions required for this action.")
    if run_checks and (not await interaction.client.tree.interaction_check(interaction) or not await command._check_can_run(interaction)):
        raise ValueError("This action is not available to you.")


async def launch(interaction, command):
    command = command.extras.get("button_target", command)
    try:
        if command.parameters:
            await check_command(interaction, command, run_checks=False)
            from core.button_flow import begin_flow
            await begin_flow(interaction, command)
        else:
            await execute(interaction, command, {})
    except (ValueError, app_commands.CheckFailure) as exc:
        await gui_send(interaction, str(exc), ephemeral=True)

    except Exception:
        logging.getLogger(__name__).exception("Could not open command buttons: %s", command.name)
        await gui_send(interaction, "The choices could not be loaded. Please reopen the action and try again.", ephemeral=True)


async def execute(interaction, command, values):
    try:
        await check_command(interaction, command)
        await gui_defer(interaction)
        # Use the same checks and callback as slash commands, with an acknowledged interaction.
        token = _ACTIVE_COMMAND.set(command)
        try:
            await command._do_call(interaction, values)
        finally:
            _ACTIVE_COMMAND.reset(token)
    except (ValueError, app_commands.CheckFailure) as exc:
        await gui_send(interaction, str(exc), ephemeral=True)
    except Exception:
        logging.getLogger(__name__).exception("Dashboard command failed: %s", command.name)
        await gui_send(interaction, "That action failed. Please try again or check the bot logs.", ephemeral=True)


async def parse_value(interaction, parameter, text):
    if not text.strip():
        if parameter.required:
            raise ValueError(f"{parameter.display_name} is required.")
        return parameter.default
    kind = parameter.type
    try:
        if kind == discord.AppCommandOptionType.integer:
            value = int(text)
        elif kind == discord.AppCommandOptionType.number:
            value = float(text)
            if not math.isfinite(value):
                raise ValueError()
        elif kind == discord.AppCommandOptionType.user:
            user_id = int(text.strip().strip("<@!>"))
            value = interaction.client.get_user(user_id) or await interaction.client.fetch_user(user_id)
        elif kind == discord.AppCommandOptionType.boolean:
            if text.casefold() not in ("true", "false", "yes", "no"):
                raise ValueError()
            value = text.casefold() in ("true", "yes")
        else:
            value = text
    except (ValueError, discord.HTTPException):
        raise ValueError(f"Enter a valid {kind.name} for {parameter.display_name}.") from None
    if kind in (discord.AppCommandOptionType.integer, discord.AppCommandOptionType.number):
        if parameter.min_value is not None and value < parameter.min_value:
            raise ValueError(f"{parameter.display_name} must be at least {parameter.min_value}.")
        if parameter.max_value is not None and value > parameter.max_value:
            raise ValueError(f"{parameter.display_name} must be at most {parameter.max_value}.")
    return await parameter.command._params[parameter.name].transform(interaction, value)


class CommandForm(discord.ui.Modal):
    def __init__(self, command, owner_id, offset=0, values=None):
        super().__init__(title=command.name.replace("_", " ").title()[:45], timeout=300)
        self.command, self.owner_id, self.offset = command, owner_id, offset
        self.values = dict(values or {})
        self.parameters = command.parameters[offset:offset + 5]
        self.used = False
        for parameter in self.parameters:
            default = parameter.default
            self.add_item(discord.ui.TextInput(
                label=parameter.display_name.replace("_", " ").title()[:45], required=parameter.required,
                default=str(default) if not parameter.required and default is not None else None,
                placeholder=(parameter.description if parameter.description != "…" else "Enter " + parameter.type.name)[:100],
                max_length=4000))

    async def on_submit(self, interaction):
        if interaction.user.id != self.owner_id or self.used:
            await gui_send(interaction, "This form is no longer available. Open /menu.", ephemeral=True)
            return
        self.used = True
        await gui_defer(interaction)
        try:
            await check_command(interaction, self.command, run_checks=False)
            for parameter, field in zip(self.parameters, self.children):
                self.values[parameter.name] = await parse_value(interaction, parameter, field.value)
        except (ValueError, app_commands.AppCommandError) as exc:
            await gui_send(interaction, str(exc) + " Reopen the action to try again.", ephemeral=True)
            return
        next_offset = self.offset + len(self.parameters)
        if next_offset < len(self.command.parameters):
            view = OwnedView(self.owner_id)
            continued = False
            async def next_page(click):
                nonlocal continued
                if continued:
                    await gui_send(click, "This form was already opened. Finish it or reopen the action.", ephemeral=True)
                    return
                continued = True
                await click.response.send_modal(CommandForm(self.command, self.owner_id, next_offset, self.values))
                for child in view.children:
                    child.disabled = True
                view.stop()
                if view.message:
                    await view.message.edit(view=view)
            view.button("Continue", next_page, style=discord.ButtonStyle.primary)
            await gui_send(interaction, "Details saved. Continue to the remaining fields.", view=view, ephemeral=True)
        else:
            await execute(interaction, self.command, self.values)

    async def on_error(self, interaction, error):
        logging.getLogger(__name__).error("GUI form failed", exc_info=(type(error), error, error.__traceback__))
        await gui_send(interaction, "The form could not be processed. Open /menu to try again.", ephemeral=True)
