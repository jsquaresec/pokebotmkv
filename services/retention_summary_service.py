class RetentionSummaryService:
    def render(self, streak: dict, missions: list[dict]) -> str:
        lines = [f"Login streak: {streak['streak']} ({streak['status']})", "Daily missions:"]
        for m in missions:
            mark = "✅" if m["complete"] else "⬜"
            lines.append(f"{mark} {m['code']} {m['progress']}/{m['target']}")
        return "\n".join(lines)
