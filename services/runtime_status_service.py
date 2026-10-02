class RuntimeStatusService:
    def snapshot(self) -> dict:
        return {
            "bot_status": "ready",
            "api_status": "ready",
            "worker_status": "ready",
            "notification_worker_status": "ready",
            "event_worker_status": "ready",
        }

    def render(self) -> str:
        snap = self.snapshot()
        return "\n".join(f"{k}: {v}" for k, v in snap.items())
