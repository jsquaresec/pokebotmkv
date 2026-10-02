import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import discord
from discord import app_commands
from core.game_gui import (CommandForm, DashboardView, OwnedView, ResultView, execute,
                           gui_send, launch, parse_value)


from gui_fakes import interaction


class GuiTests(unittest.IsolatedAsyncioTestCase):
    async def test_cards_paginate_without_losing_text(self):
        click = interaction()
        text = "x" * 9000
        await gui_send(click, text)
        view = click.response.send_message.await_args.kwargs["view"]
        self.assertIsInstance(view, ResultView)
        self.assertEqual("".join(view.pages), text)
        self.assertLessEqual(len(view.embed().description), 4096)

    async def test_preserves_custom_embed_and_view(self):
        click = interaction(done=True)
        embed, view = discord.Embed(title="Catch"), discord.ui.View()
        await gui_send(click, embed=embed, view=view)
        self.assertIs(click.edit_original_response.await_args.kwargs["embeds"][0], embed)
        self.assertIs(click.edit_original_response.await_args.kwargs["view"], view)
        click.followup.send.assert_not_awaited()

    async def test_restricts_navigation_to_owner(self):
        view = OwnedView(2)
        self.assertFalse(await view.interaction_check(interaction()))

    async def test_permission_check_blocks_callback(self):
        calls = []
        @app_commands.command(name="restricted", description="Test")
        @app_commands.default_permissions(manage_guild=True)
        async def command(i):
            calls.append(i)
        await execute(interaction(), command, {})
        self.assertEqual(calls, [])

    async def test_command_checks_run_once(self):
        check = AsyncMock(return_value=True)
        calls = []
        @app_commands.command(name="test_action", description="Test")
        @app_commands.check(check)
        async def command(i):
            calls.append(i)
        click = interaction()
        await launch(click, command)
        check.assert_awaited_once()
        self.assertEqual(calls, [click])
        click.response.defer.assert_awaited_once()

    async def test_numeric_range_and_optional_defaults(self):
        @app_commands.command(name="test_form", description="Test")
        async def command(i, amount: app_commands.Range[int, 1, 20], label: str | None = None):
            pass
        amount, label = command.parameters
        self.assertEqual(await parse_value(interaction(), amount, "5"), 5)
        self.assertIsNone(await parse_value(interaction(), label, ""))
        for value in ("0", "21", "abc"):
            with self.assertRaises(ValueError):
                await parse_value(interaction(), amount, value)

    async def test_six_field_form_uses_two_pages(self):
        @app_commands.command(name="party", description="Test")
        async def command(i, slot1: int, slot2: int = 0, slot3: int = 0,
                          slot4: int = 0, slot5: int = 0, slot6: int = 0):
            pass
        first = CommandForm(command, 1)
        second = CommandForm(command, 1, offset=5, values={"slot1": 42})
        self.assertEqual(len(first.children), 5)
        self.assertEqual(len(second.children), 1)
        self.assertEqual(second.values["slot1"], 42)

    async def test_hidden_admin_commands_do_not_appear(self):
        async def callback(i):
            pass
        callback.__module__ = "cogs.admin_debug"
        command = app_commands.Command(name="debug_test", description="Test", callback=callback)
        view = DashboardView(interaction(commands=[command]))
        self.assertEqual(len(view.children), 0)
        view = DashboardView(interaction(admin=True, commands=[command]))
        self.assertEqual(view.children[0].label, "Admin & Previews")

    async def test_command_buttons_open_without_executing(self):
        calls = []
        @app_commands.command(name="test_form", description="Test")
        async def command(i, amount: int):
            calls.append(amount)
        click = interaction()
        with patch('core.button_flow.begin_flow', new_callable=AsyncMock) as begin:
            await launch(click, command)
            begin.assert_awaited_once_with(click, command)
        click.response.send_modal.assert_not_awaited()
        self.assertEqual(calls, [])
