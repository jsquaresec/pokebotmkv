from core.maintenance import maintenance_mode_enabled

class MaintenanceService:
    def ensure_available(self) -> None:
        if maintenance_mode_enabled():
            raise ValueError("Service is currently in maintenance mode")
