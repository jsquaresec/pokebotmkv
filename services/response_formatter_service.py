class ResponseFormatterService:
    def section(self, title: str, body: str) -> str:
        return f"**{title}**\n{body}"

    def bullet_lines(self, items: list[str]) -> str:
        return "\n".join(f"• {item}" for item in items)

    def success(self, msg: str) -> str:
        return f"✅ {msg}"

    def warning(self, msg: str) -> str:
        return f"⚠️ {msg}"

    def error(self, msg: str) -> str:
        return f"❌ {msg}"
