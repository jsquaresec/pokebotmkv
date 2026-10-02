import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from core.party_builder import PartyBuilder


from gui_fakes import interaction, message

def click():
    return interaction(source=message(message_id=90), done=True)


class PartyBuilderTests(unittest.IsolatedAsyncioTestCase):
    def make(self, selected=()):
        mons = [SimpleNamespace(id=i, display_name=f"Pokémon {i}", level=i) for i in range(1, 26)]
        save = AsyncMock(return_value=True)
        return PartyBuilder(1, mons, selected, save), save

    async def test_selection_is_ordered_and_limited_to_six(self):
        view, _ = self.make()
        for i in range(7):
            await view.children[i].callback(click())
        self.assertEqual(view.selected, [1, 2, 3, 4, 5, 6])
        await view.children[0].callback(click())
        await view.children[6].callback(click())
        self.assertEqual(view.selected, [2, 3, 4, 5, 6, 7])

    async def test_paging_keeps_selection(self):
        view, _ = self.make([2])
        self.assertEqual(len(view.children), 25)
        await next(b for b in view.children if b.label == "Next").callback(click())
        await view.children[0].callback(click())
        self.assertEqual(view.selected, [2, 21])

    async def test_cancel_and_clear_do_not_save(self):
        view, save = self.make([1])
        await view.clear(click())
        self.assertEqual(view.selected, [])
        await view.cancel(click())
        save.assert_not_awaited()
        self.assertTrue(all(b.disabled for b in view.children))

    async def test_duplicate_save_only_writes_once(self):
        view, save = self.make([3, 1])
        await asyncio.gather(view.save(click()), view.save(click()))
        save.assert_awaited_once()
        self.assertEqual(save.await_args.args[1], [3, 1])

    async def test_failed_save_keeps_editor_open(self):
        view, save = self.make([1])
        save.return_value = False
        await view.save(click())
        self.assertFalse(view.closed)

    async def test_expired_editor_cannot_save(self):
        view, save = self.make([1])
        await view.on_timeout()
        await view.save(click())
        save.assert_not_awaited()
