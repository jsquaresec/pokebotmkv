from config import settings

def redis_enabled() -> bool:
    return settings.enable_redis

def dashboard_api_enabled() -> bool:
    return settings.enable_dashboard_api
