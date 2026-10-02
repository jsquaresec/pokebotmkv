class UnifiedActionResponseService:
    def success(self, title: str, body: str) -> str:
        return f"✅ {title}\n{body}"

    def warning(self, title: str, body: str) -> str:
        return f"⚠️ {title}\n{body}"

    def error(self, title: str, body: str) -> str:
        return f"❌ {title}\n{body}"

    def next_steps(self, steps: list[str]) -> str:
        if not steps:
            return ""
        return "Next:\n" + "\n".join(f"→ {s}" for s in steps)
