import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from core.encounter_buttons import EncounterButtons
from services.encounter_v70_service import EncounterV70Service
from services.encounter_ui import encounter_card, caught_card, registry


def click(user_id=1):
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id),
        response=SimpleNamespace(defer=AsyncMock(), is_done=Mock(return_value=True)),
        followup=SimpleNamespace(send=AsyncMock()),
        message=SimpleNamespace(edit=AsyncMock()),
    )


class EncounterButtonTests(unittest.IsolatedAsyncioTestCase):
    async def test_ball_uses_clicked_encounter_and_disables_after_catch(self):
        catch = AsyncMock(return_value=SimpleNamespace(species="Pikachu"))
        view = EncounterButtons(42, AsyncMock(), catch, 300)
        button = view.children[1]
        await asyncio.gather(button.callback(click(1)), button.callback(click(2)))
        self.assertEqual(catch.await_count, 1)
        self.assertEqual(catch.await_args.args[1:], ("poke_ball", 42))
        self.assertTrue(all(button.disabled for button in view.children))

    async def test_failed_catch_allows_another_player_to_try(self):
        catch = AsyncMock(return_value=None)
        view = EncounterButtons(42, AsyncMock(), catch, 300)
        await view.children[2].callback(click(1))
        await view.children[3].callback(click(2))
        self.assertEqual(catch.await_count, 2)
        self.assertFalse(view.closed)

    async def test_catch_results_and_errors_edit_without_new_messages(self):
        for outcome in (None, SimpleNamespace(species="Pikachu"), ValueError("You do not have a poke_ball.")):
            catch = AsyncMock(side_effect=outcome) if isinstance(outcome, Exception) else AsyncMock(return_value=outcome)
            view = EncounterButtons(42, AsyncMock(), catch, 300)
            interaction = click()
            await view.children[1].callback(interaction)
            interaction.response.defer.assert_awaited_once_with(thinking=False)
            interaction.followup.send.assert_not_awaited()
            interaction.message.edit.assert_awaited_once()
            self.assertFalse(catch.await_args.kwargs["notify"])

    async def test_weaken_updates_health(self):
        attack = AsyncMock(return_value=SimpleNamespace(species="Pikachu", level=5, current_hp=5, max_hp=20))
        view = EncounterButtons(42, attack, AsyncMock(), 300)
        interaction = click()
        await view.children[0].callback(interaction)
        self.assertEqual(attack.await_args.args[1], 42)
        embed = interaction.message.edit.await_args.kwargs["embed"]
        self.assertIn("5/20 HP", embed.fields[0].value)
        interaction.followup.send.assert_not_awaited()
        self.assertFalse(attack.await_args.kwargs["notify"])

    async def test_old_buttons_cannot_consume_balls_for_new_spawn(self):
        service = object.__new__(EncounterV70Service)
        service.repo = SimpleNamespace(active_in_channel=AsyncMock(return_value=SimpleNamespace(id=43)))
        users, inventory = Mock(), Mock()
        with self.assertRaisesRegex(ValueError, "ended"):
            await service.attempt_catch(1, 2, "master_ball", users, inventory, encounter_id=42)
        inventory.get_item_locked.assert_not_called()
        with self.assertRaisesRegex(ValueError, "ended"):
            await service.attack(1, 10, encounter_id=42)


class CatchProbabilityTests(unittest.TestCase):
    def setUp(self):
        self.service = object.__new__(EncounterV70Service)
        self.service.registry = SimpleNamespace(species=lambda name: {"catch_rate": 120})

    def chance(self, hp, ball="poke_ball"):
        row = SimpleNamespace(species="Example", current_hp=hp, max_hp=100)
        return self.service.catch_probability(row, ball)

    def test_lower_health_strongly_increases_probability(self):
        chances = [self.chance(hp) for hp in (100, 75, 50, 25, 1)]
        self.assertEqual(chances, sorted(chances))
        self.assertAlmostEqual(chances[0], 120 / 255 * 0.35)
        self.assertGreater(chances[-1], chances[0] * 5)

    def test_ball_bonuses_and_caps_are_preserved(self):
        self.assertLess(self.chance(100), self.chance(100, "great_ball"))
        self.assertLess(self.chance(100, "great_ball"), self.chance(100, "ultra_ball"))
        self.assertEqual(self.chance(1, "ultra_ball"), 0.95)
        self.assertEqual(self.chance(100, "master_ball"), 1.0)
        with self.assertRaisesRegex(ValueError, "Unknown"):
            self.chance(100, "invalid_ball")


class EncounterCardTests(unittest.TestCase):
    def test_card_odds_match_catching_service(self):
        row = SimpleNamespace(species="Pikachu", level=5, current_hp=5, max_hp=20, rarity="common")
        embed = encounter_card(row)
        service = EncounterV70Service(None, registry=registry())
        self.assertIn(f'{service.catch_probability(row, "poke_ball"):.0%}', embed.fields[1].value)
        self.assertIn("100%", embed.fields[1].value)
        self.assertTrue(embed.thumbnail.url.endswith('/25.png'))
        self.assertLess(len(embed), 6000)

    def test_finished_cards_remove_live_odds(self):
        row = SimpleNamespace(species="Pikachu", level=5, current_hp=5, max_hp=20, rarity="common")
        expired = encounter_card(row, expired=True)
        self.assertFalse(any(field.name == "Catch chance" for field in expired.fields))
        caught = caught_card(row, 123)
        self.assertIn("<@123>", caught.description)
        self.assertIn("500", caught.fields[0].value)
