class EventAnnouncementService:
    def start_message(self, code: str) -> str:
        return f"📣 Live event started: **{code}**!"

    def end_message(self, code: str) -> str:
        return f"⏹️ Live event ended: **{code}**."

    def status_message(self, active_codes: list[str]) -> str:
        if not active_codes:
            return "No live events are active."
        joined = ", ".join(active_codes)
        return f"Active events: {joined}"
