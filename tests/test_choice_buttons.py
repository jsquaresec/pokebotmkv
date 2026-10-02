import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from core.choice_buttons import ChoiceButtons, choose


from gui_fakes import interaction


class ChoiceButtonTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # This file is also executed directly by the legacy script runner.
        from core.private_panels import PANELS, LOCKS
        PANELS.clear()
        LOCKS.clear()

    async def test_duplicate_click_runs_action_once(self):
        action = AsyncMock()
        view = ChoiceButtons(1, [("Buy", "poke_ball")], action)
        button = view.children[0]
        await asyncio.gather(button.callback(interaction()), button.callback(interaction()))
        self.assertEqual(action.await_count, 1)
        self.assertEqual(action.await_args.args[1], "poke_ball")
        self.assertTrue(button.disabled)
        self.assertTrue(view.is_finished())

    async def test_other_player_cannot_use_menu(self):
        view = ChoiceButtons(1, [("Buy", "poke_ball")], AsyncMock())
        click = interaction(2)
        self.assertFalse(await view.interaction_check(click))
        click.response.send_message.assert_awaited_once()
        self.assertFalse(view.used)

    async def test_pagination_preserves_values(self):
        action = AsyncMock()
        view = ChoiceButtons(1, [(str(i), i) for i in range(45)], action)
        self.assertEqual(len(view.children), 22)
        self.assertTrue(view.children[-2].disabled)
        await view.children[-1].callback(interaction())
        self.assertEqual(view.page, 1)
        await view.children[0].callback(interaction())
        self.assertEqual(action.await_args.args[1], 20)

    async def test_expiry_disables_menu_and_blocks_action(self):
        action = AsyncMock()
        view = ChoiceButtons(1, [("Buy", "poke_ball")], action)
        view.message = SimpleNamespace(edit=AsyncMock())
        await view.on_timeout()
        self.assertTrue(view.children[0].disabled)
        await view.children[0].callback(interaction())
        action.assert_not_awaited()
        view.message.edit.assert_awaited_once()

    async def test_empty_menu_is_explained(self):
        click = interaction()
        await choose(click, "Pick", [], AsyncMock())
        self.assertIn("No available options", click.response.send_message.await_args.kwargs["embeds"][0].description)

    async def test_menu_edits_deferred_response(self):
        click = interaction(done=True)
        await choose(click, "Pick", [("One", 1)], AsyncMock())
        click.followup.send.assert_not_awaited()
        click.edit_original_response.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
