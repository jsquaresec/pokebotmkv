from core.game_gui import gui_send
import discord
from discord import app_commands
from discord.ext import commands
from config import settings
from core.database import SessionLocal
from repositories.users import UserRepository
from repositories.queue_entries import QueueEntryRepository
from repositories.ranked_profiles import RankedProfileRepository
from repositories.audit_logs import AuditLogRepository
from repositories.notification_deliveries import NotificationDeliveryRepository
from services.queue_service import QueueService
from services.audit_service import AuditService
from services.redis_queue_service import RedisQueueService
from services.notification_service import NotificationService
from services.ranked_tier_service import RankedTierService
from services.leaderboard_service import LeaderboardService
from services.live_event_toggle_service import LiveEventToggleService
from services.season_service import SeasonService

_EVENT_FLAGS = LiveEventToggleService()
_SEASON = SeasonService()

class RankedCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.redis_queue = RedisQueueService()
        self.tiers = RankedTierService()
        self.leaderboard = LeaderboardService()

    async def _get_or_create_ranked_profile(self, session, owner_id: int):
        ranked_repo = RankedProfileRepository(session)
        profile = await ranked_repo.get_by_owner(owner_id)
        if profile:
            return profile
        return await ranked_repo.create(owner_id, settings.ranked_start_rating)

    @app_commands.command(name="ranked_join", description="Join ranked queue")
    async def ranked_join(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            queue_repo = QueueEntryRepository(session)
            audit = AuditService(AuditLogRepository(session))
            user = await user_repo.get_by_discord_id_locked(interaction.user.id)
            if user is None:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            from sqlalchemy import select
            from models.pokemon import PokemonInstance
            from models.party import PartySlot
            busy = (await session.execute(select(PokemonInstance.id).join(
                PartySlot, PartySlot.pokemon_id == PokemonInstance.id).where(
                PartySlot.owner_id == user.id, PokemonInstance.locked.is_(True)).limit(1))).scalar_one_or_none()
            if busy is not None:
                await gui_send(interaction, "Finish your wild battle before joining ranked.", ephemeral=True)
                return
            profile = await self._get_or_create_ranked_profile(session, user.id)
            queue_service = QueueService(queue_repo)
            result = await queue_service.join_or_match(interaction.user.id, profile.rating)

            if result["status"] == "already_queued":
                await gui_send(interaction, "You are already queued.", ephemeral=True)
                return

            tier = self.tiers.tier_for_rating(profile.rating)

            if result["status"] == "queued":
                await audit.log("ranked_join_queue", interaction.user.id, None, f"rating={profile.rating}")
                await self.redis_queue.push("queue_events", {"type": "ranked_join", "discord_id": interaction.user.id, "rating": profile.rating})
                await gui_send(interaction, f"You joined ranked queue at rating **{profile.rating}** ({tier}).")
                return

            p1_discord_id, p2_discord_id = result["players"]
            await audit.log("ranked_match_pair_detected", interaction.user.id, None, f"p1={p1_discord_id},p2={p2_discord_id}")
            await gui_send(interaction, f"Players paired: <@{p1_discord_id}> vs <@{p2_discord_id}>.")

    @app_commands.command(name="ranked_profile", description="View your ranked profile")
    async def ranked_profile(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_discord_id(interaction.user.id)
            if user is None:
                await gui_send(interaction, "Use `/start` first.", ephemeral=True)
                return
            profile = await self._get_or_create_ranked_profile(session, user.id)
            tier = self.tiers.tier_for_rating(profile.rating)
            reward = _SEASON.reward_for_tier(tier)
            await gui_send(interaction, 
                f"Rating: **{profile.rating}** | Tier: **{tier}** | Wins: **{profile.wins}** | Losses: **{profile.losses}**\n"
                f"Projected season reward: **{reward['coins']} coins** | Title: **{reward['title']}**"
            )

    @app_commands.command(name="leaderboard", description="View the global leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            ranked_repo = RankedProfileRepository(session)
            rows = await ranked_repo.top_profiles(10)
            if not rows:
                await gui_send(interaction, "No leaderboard data yet.", ephemeral=True)
                return
            lines = [
                f"#{i} Owner {row.owner_id} | Rating {row.rating} | Tier {self.tiers.tier_for_rating(row.rating)} | W {row.wins} L {row.losses}"
                for i, row in enumerate(rows, start=1)
            ]
            await gui_send(interaction, "\n".join(lines))

    @app_commands.command(name="season_status", description="View current season status")
    async def season_status(self, interaction: discord.Interaction):
        snap = _SEASON.snapshot()
        await gui_send(interaction, 
            f"Season: **{snap['season_name']}**\nEnds: **{snap['ends_at']}**\nDays remaining: **{snap['days_remaining']}**",
            ephemeral=True,
        )

    @app_commands.command(name="ranked_notifications", description="Show your recent matchmaking notifications")
    async def ranked_notifications(self, interaction: discord.Interaction):
        async with SessionLocal() as session:
            service = NotificationService(NotificationDeliveryRepository(session))
            rows = await service.recent_for_recipient(interaction.user.id, 10)
            if not rows:
                await gui_send(interaction, "No notifications yet.", ephemeral=True)
                return
            lines = [f'#{row.id} {row.event_type} | battle={row.related_battle_id} | status={row.status} | retries={row.retry_count}' for row in rows]
            await gui_send(interaction, "\n".join(lines[:10]), ephemeral=True)

    @app_commands.command(name="events_status", description="Show current live event toggles")
    async def events_status(self, interaction: discord.Interaction):
        flags = _EVENT_FLAGS.status()
        lines = [f"{k}: {'ON' if v else 'OFF'}" for k, v in flags.items()]
        await gui_send(interaction, "\n".join(lines), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(RankedCog(bot))
