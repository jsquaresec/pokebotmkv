import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord
from discord import app_commands
from discord.ext import commands

from core.button_flow import ButtonFlow, CustomValue, install_button_commands
from core.game_gui import category_for
from services.button_options import options_for


from gui_fakes import interaction, message

def click():
    return interaction(source=message(message_id=90), admin=True, done=True)


def button(view, label):
    return next(child for child in view.children if child.label == label)


class ButtonFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_selection_review_and_duplicate_execution(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, amount: app_commands.Range[int, 1, 20]):
            pass
        flow = ButtonFlow(command, 1)
        with patch('core.button_flow.execute', new_callable=AsyncMock) as execute:
            await flow.show(click())
            first = flow.view
            await button(first, "5").callback(click())
            self.assertEqual(flow.values, {"amount": 5})
            await button(first, "10").callback(click())  # stale menu cannot overwrite
            self.assertEqual(flow.values, {"amount": 5})
            run = button(flow.view, "Run Action")
            await asyncio.gather(run.callback(click()), run.callback(click()))
            execute.assert_awaited_once()
            self.assertEqual(execute.await_args.args[2], {"amount": 5})

    async def test_back_discards_dependent_selections(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, amount: int, hours: int):
            pass
        flow = ButtonFlow(command, 1)
        await flow.show(click())
        await button(flow.view, "100").callback(click())
        await button(flow.view, "6").callback(click())
        await button(flow.view, "Back").callback(click())
        self.assertEqual(flow.values, {"amount": 100})
        await button(flow.view, "Back").callback(click())
        self.assertEqual(flow.values, {})

    async def test_cancel_never_executes(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, amount: int):
            pass
        flow = ButtonFlow(command, 1)
        with patch('core.button_flow.execute', new_callable=AsyncMock) as execute:
            await flow.show(click())
            await button(flow.view, "Cancel").callback(click())
            self.assertTrue(flow.closed)
            execute.assert_not_awaited()

    async def test_pagination_preserves_record_id(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, pokemon_id: int):
            pass
        flow = ButtonFlow(command, 1)
        options = [(f"Pokémon {n}", n) for n in range(45)]
        with patch('core.button_flow.options_for', new_callable=AsyncMock, return_value=(options, False)):
            await flow.show(click())
            self.assertLessEqual(len(flow.view.children), 25)
            await button(flow.view, "Next").callback(click())
            await button(flow.view, "Pokémon 20").callback(click())
            self.assertEqual(flow.values["pokemon_id"], 20)

    async def test_optional_default_and_invalid_custom(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, amount: app_commands.Range[int, 1, 20] = 5):
            pass
        flow = ButtonFlow(command, 1)
        await flow.show(click())
        await flow.select(click(), "999", "999")
        self.assertEqual(flow.index, 0)
        self.assertEqual(flow.values, {})
        await button(flow.view, "Default: 5").callback(click())
        self.assertEqual(flow.values["amount"], 5)

    async def test_custom_dialog_is_invalidated_by_new_selection(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, amount: int):
            pass
        flow = ButtonFlow(command, 1)
        await flow.show(click())
        modal = CustomValue(flow, flow.version)
        modal.field._value = "999"
        await button(flow.view, "100").callback(click())
        await modal.on_submit(click())
        self.assertEqual(flow.values, {"amount": 100})

    async def test_wrappers_keep_category_permissions_and_original(self):
        async def action(i, pokemon_id: int):
            pass
        action.__module__ = "cogs.market"
        original = app_commands.Command(name="market_list", description="Test", callback=action)
        original.guild_only = True
        original.default_permissions = discord.Permissions(manage_guild=True)
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
        async with bot:
            bot.tree.add_command(original)
            install_button_commands(bot)
            entry = bot.tree.get_command("market_list")
            self.assertEqual(entry.parameters, [])
            self.assertIs(entry.extras["button_target"], original)
            self.assertEqual(category_for(entry), "Shop & Trading")
            self.assertTrue(entry.guild_only)
            self.assertEqual(entry.default_permissions, original.default_permissions)
            install_button_commands(bot)
            self.assertIs(bot.tree.get_command("market_list"), entry)

    async def test_boolean_and_numeric_presets(self):
        @app_commands.command(name="test_action", description="Test")
        async def command(i, shiny: bool, min_iv: app_commands.Range[float, 0, 100]):
            pass
        choices, custom = await options_for(click(), command, command.parameters[0], {})
        self.assertEqual(choices, [("Yes", True), ("No", False)])
        self.assertFalse(custom)
        choices, custom = await options_for(click(), command, command.parameters[1], {})
        self.assertTrue(all(0 <= n <= 100 for _, n in choices))
        self.assertTrue(custom)
