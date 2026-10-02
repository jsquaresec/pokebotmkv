from core.game_gui import gui_send, gui_defer
from core.choice_buttons import choose, reply
import discord
from discord import app_commands
from discord.ext import commands
from core.database import SessionLocal
from repositories.active_battles import ActiveBattleRepository
from repositories.users import UserRepository
from repositories.pokemon import PokemonRepository
from repositories.ranked_profiles import RankedProfileRepository
from repositories.battle_replays import BattleReplayRepository
from repositories.audit_logs import AuditLogRepository
from repositories.reward_claims import RewardClaimRepository
from services.battle_service import BattleService
from services.battle_action_service import BattleActionService
from services.move_service import MoveService
from services.battle_rules_service import BattleRulesService
from services.battle_embed_service import BattleEmbedService
from services.persistence_service import PersistenceService
from services.replay_service import ReplayService
from services.ranked_service import RankedService
from services.maintenance_service import MaintenanceService
from services.audit_service import AuditService
from services.reward_service import RewardService
from services.progression_apply_service import ProgressionApplyService
from services.battle_result_service import BattleResultService
from services.battle_timer_service import BattleTimerService
from services.battle_ui_service import BattleUIService

_TIMERS = BattleTimerService()

class BattleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.maintenance = MaintenanceService()
        self.action_service = BattleActionService()
        self.move_service = MoveService()
        self.rules = BattleRulesService()
        self.render = BattleEmbedService()
        self.progression = ProgressionApplyService()
        self.results = BattleResultService()
        self.ui = BattleUIService()

    @app_commands.command(name="battle_status", description="View your current active battle")
    async def battle_status(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle = await repo.get_for_user(interaction.user.id)
            if battle is None:
                await gui_send(interaction, "You do not have an active battle.", ephemeral=True)
                return
            state = BattleService(repo).load_state(battle)
            remaining = _TIMERS.remaining(battle.id)
            await gui_send(interaction, self.render.render_summary_text(battle.id, state) + f"\nTurn timer: {remaining}s")

    @app_commands.command(name="battle_view", description="Render a cleaner battle view")
    async def battle_view(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle = await repo.get_for_user(interaction.user.id)
            if battle is None:
                await gui_send(interaction, "No active battle.", ephemeral=True)
                return
            state = BattleService(repo).load_state(battle)
            await gui_send(interaction, self.ui.render_battle_view(battle.id, state, _TIMERS.remaining(battle.id)))

    @app_commands.command(name="battle_move", description="Submit a move in your active battle")
    async def battle_move(self, interaction: discord.Interaction):
        await gui_defer(interaction, ephemeral=True, thinking=True)
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle = await repo.get_for_user(interaction.user.id)
            if battle is None:
                await reply(interaction, "You do not have an active battle.", ephemeral=True)
                return
            state = BattleService(repo).load_state(battle)
            key = "player_one" if state["player_one"]["discord_id"] == interaction.user.id else "player_two"
            active = state[key]["active"]
            moves = self.rules.moves.moves_for_species_level(active["name"], active["level"])
            battle_id, turn = battle.id, state["turn"]

        async def submit(click, move):
            await self.select_move(click, move, battle_id, turn)

        await choose(interaction, "Choose your battle move.", [(name, name) for name in moves], submit)

    async def select_move(self, interaction, move_name, expected_battle, expected_turn):
        try:
            self.maintenance.ensure_available()
        except ValueError as exc:
            await reply(interaction, str(exc), ephemeral=True)
            return

        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle_service = BattleService(repo)
            audit = AuditService(AuditLogRepository(session))
            battle = await repo.get_for_user(interaction.user.id)
            if battle is None:
                await reply(interaction, "You do not have an active battle.", ephemeral=True)
                return
            state = battle_service.load_state(battle)
            if battle.id != expected_battle or state["turn"] != expected_turn:
                await reply(interaction, "The battle changed. Open /battle_move again.", ephemeral=True)
                return
            try:
                actor_key = "player_one" if state["player_one"]["discord_id"] == interaction.user.id else "player_two"
                active_species = state[actor_key]["active"]["name"]
                active_level = state[actor_key]["active"]["level"]
                chosen = move_name.strip() or self.move_service.default_move_for(active_species)
                chosen = self.rules.validate_move_choice(active_species, active_level, chosen)
                state = self.action_service.submit_move(state, interaction.user.id, chosen)
                await audit.log("battle_action_submitted", interaction.user.id, battle.id, f"move={chosen}")
                _TIMERS.start_turn(battle.id, 30)
                if self.action_service.both_ready(state):
                    state = battle_service.apply_move(state, interaction.user.id)
                    await audit.log("battle_turn_resolved", interaction.user.id, battle.id, f'turn={state["turn"]}')
                    _TIMERS.start_turn(battle.id, 30)
                await battle_service.save_state(battle, state)
            except ValueError as exc:
                await reply(interaction, str(exc), ephemeral=True)
                return
            await reply(interaction, self.render.render_log_tail(state, 10))

    @app_commands.command(name="battle_timer", description="Check remaining turn time")
    async def battle_timer(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            repo = ActiveBattleRepository(session)
            battle = await repo.get_for_user(interaction.user.id)
            if battle is None:
                await gui_send(interaction, "No active battle.", ephemeral=True)
                return
            await gui_send(interaction, f"Time remaining: {_TIMERS.remaining(battle.id)}s", ephemeral=True)

    @app_commands.command(name="battle_finalize", description="Finalize a finished battle")
    async def battle_finalize(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            active_repo = ActiveBattleRepository(session)
            replay_repo = BattleReplayRepository(session)
            user_repo = UserRepository(session)
            pokemon_repo = PokemonRepository(session)
            ranked_repo = RankedProfileRepository(session)
            reward_repo = RewardClaimRepository(session)
            audit = AuditService(AuditLogRepository(session))
            rewards = RewardService(reward_repo)

            battle = await active_repo.get_for_user(interaction.user.id)
            if battle is None:
                await gui_send(interaction, "You do not have an active battle.", ephemeral=True)
                return

            battle_service = BattleService(active_repo)
            state = battle_service.load_state(battle)
            if not state["finished"]:
                await gui_send(interaction, "This battle is not finished yet.", ephemeral=True)
                return

            persistence = PersistenceService(pokemon_repo)
            await persistence.sync_battle_hp({"player_one": state["player_one"]["active"], "player_two": state["player_two"]["active"]})
            replay_service = ReplayService(replay_repo)
            await replay_service.save_replay(battle.id, battle.battle_type, state)

            reward_msg = ""
            winner_name = None
            if battle.battle_type == "ranked" and state["winner_discord_id"] is not None:
                winner_user = await user_repo.get_by_discord_id(state["winner_discord_id"])
                loser_discord_id = battle.player_two_discord_id if state["winner_discord_id"] == battle.player_one_discord_id else battle.player_one_discord_id
                loser_user = await user_repo.get_by_discord_id(loser_discord_id)
                if winner_user and loser_user:
                    winner_name = winner_user.username
                    winner_profile = await ranked_repo.get_by_owner(winner_user.id)
                    loser_profile = await ranked_repo.get_by_owner(loser_user.id)
                    if winner_profile and loser_profile:
                        ranked = RankedService()
                        winner_new, loser_new = ranked.apply_result(winner_profile.rating, loser_profile.rating, 1.0)
                        winner_profile.rating = winner_new
                        loser_profile.rating = loser_new
                        winner_profile.wins += 1
                        loser_profile.losses += 1
                        await session.commit()
                    winner_user.balance += 100
                    await session.commit()
                    await rewards.grant_battle_win(state["winner_discord_id"], battle.id, 100, 50)
                    winner_active = state["player_one"]["active"] if state["winner_discord_id"] == state["player_one"]["discord_id"] else state["player_two"]["active"]
                    mon = await pokemon_repo.get_by_id(winner_active["pokemon_id"])
                    leveled_msg = ""
                    if mon is not None:
                        result = self.progression.apply_battle_xp_to_party_member(mon, 200)
                        await pokemon_repo.session.commit()
                        if result["leveled"]:
                            leveled_msg = f'{mon.species} leveled to {result["new_level"]}.'
                            if result["unlocked_moves"]:
                                leveled_msg += f' Learned: {", ".join(result["unlocked_moves"])}.'
                    reward_msg = self.results.render_result(battle.id, winner_name, 100, 50, leveled_msg)

            battle.finished = True
            _TIMERS.clear(battle.id)
            await session.commit()
            await audit.log("battle_finalized", interaction.user.id, battle.id, f'winner={state["winner_discord_id"]}')
            await gui_send(interaction, reward_msg or f"Battle #{battle.id} finalized and replay saved.")

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleCog(bot))
