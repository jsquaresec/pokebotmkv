import discord
from discord.ext import commands
from config import settings
from core.logging_setup import configure_logging
from core.database import init_models, SessionLocal
from services.startup_recovery_service import StartupRecoveryService

__version__ = "90.0.0"

COGS = [
    "cogs.gui",
    "cogs.profile",
    "cogs.catch",
    "cogs.pokemon",
    "cogs.party",
    "cogs.ranked",
    "cogs.battle",
    "cogs.replay",
    "cogs.cosmetics",
    "cogs.live_events",
    "cogs.admin",
    "cogs.economy",
    "cogs.encounters",
    "cogs.market",
    "cogs.content",
    "cogs.onboarding",
    "cogs.retention",
    "cogs.regions",
    "cogs.events",
    "cogs.guild",
    "cogs.trainer_v80",
    "cogs.auctions",
    "cogs.social",
    "cogs.season_pass",
    "cogs.system_v80",
]

DEBUG_COGS = ["cogs.admin_debug", "cogs.admin_playtest"]
PREVIEW_COGS = ["cogs.ui_preview", "cogs.balance_preview"]

class PokeBot(commands.Bot):
    async def setup_hook(self) -> None:
        from services.content_registry_v70 import ContentRegistryV70
        errors = ContentRegistryV70().validate()
        if errors:
            raise RuntimeError("Invalid Pokémon catalog: " + "; ".join(errors[:10]))
        await init_models()

        async with SessionLocal() as session:
            from services.wild_battle_service import WildBattleService
            await WildBattleService.expire(session)
            from services.catalog_upgrade_service import CatalogUpgradeService
            updated = await CatalogUpgradeService().upgrade_available(session)
            await session.commit()
            print(f"Updated {updated} Pokémon to the complete species catalog.")
            recovery = StartupRecoveryService()
            rows = await recovery.scan_active_battles(session)
            print(f"Startup recovery scan found {len(rows)} unfinished battle(s).")

        extensions = list(COGS)
        if settings.enable_debug_cogs:
            extensions.extend(DEBUG_COGS)
        if settings.enable_preview_cogs:
            extensions.extend(PREVIEW_COGS)
        for cog in extensions:
            await self.load_extension(cog)
        from core.button_flow import install_button_commands
        install_button_commands(self)
        await self.tree.sync()

async def run_bot() -> None:
    configure_logging(settings.log_level)
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = PokeBot(command_prefix=settings.bot_prefix, intents=intents)

    @bot.event
    async def on_ready():
        await bot.change_presence(
            activity=discord.Game(name="Built By MkingV92"),
            status=discord.Status.online,
        )
        print(f"Logged in as {bot.user} (ID: {bot.user.id})")

    @bot.command(name="ping")
    async def ping(ctx: commands.Context):
        latency_ms = round(bot.latency * 1000)
        await ctx.send(f"Pong! {latency_ms}ms")

    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is missing. Set it in your .env file.")

    await bot.start(settings.discord_token)
