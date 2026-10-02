from config import settings

def maintenance_mode_enabled() -> bool:
    return settings.enable_maintenance_mode
