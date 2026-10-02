import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(slots=True)
class Settings:
    api_token: str = os.getenv("API_TOKEN", "")
    discord_token: str = os.getenv("DISCORD_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/pokebot")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    bot_prefix: str = os.getenv("BOT_PREFIX", "!")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    ranked_start_rating: int = int(os.getenv("RANKED_START_RATING", "1000"))
    ranked_k_factor: int = int(os.getenv("RANKED_K_FACTOR", "32"))
    enable_maintenance_mode: bool = os.getenv("ENABLE_MAINTENANCE_MODE", "false").lower() == "true"
    enable_dashboard_api: bool = os.getenv("ENABLE_DASHBOARD_API", "true").lower() == "true"
    enable_redis: bool = os.getenv("ENABLE_REDIS", "true").lower() == "true"
    notification_max_retries: int = int(os.getenv("NOTIFICATION_MAX_RETRIES", "3"))
    auto_create_schema: bool = os.getenv("AUTO_CREATE_SCHEMA", "false").lower() == "true"
    enable_debug_cogs: bool = os.getenv("ENABLE_DEBUG_COGS", "false").lower() == "true"
    enable_preview_cogs: bool = os.getenv("ENABLE_PREVIEW_COGS", "false").lower() == "true"
    spawn_message_threshold: int = int(os.getenv("SPAWN_MESSAGE_THRESHOLD", "20"))
    encounter_ttl_seconds: int = int(os.getenv("ENCOUNTER_TTL_SECONDS", "300"))

settings = Settings()
