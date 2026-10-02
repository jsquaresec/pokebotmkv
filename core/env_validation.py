from config import settings

def validate_environment() -> None:
    errors = []

    if not settings.discord_token:
        errors.append("DISCORD_TOKEN is missing")
    if not settings.database_url:
        errors.append("DATABASE_URL is missing")
    if not settings.redis_url:
        errors.append("REDIS_URL is missing")

    if errors:
        raise RuntimeError("Environment validation failed: " + "; ".join(errors))
