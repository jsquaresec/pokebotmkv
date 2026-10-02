class PremiumEmbedThemeService:
    RARITY_COLORS = {
        "common": "gray",
        "uncommon": "green",
        "rare": "blue",
        "epic": "purple",
        "legendary": "gold",
    }

    def color_for_rarity(self, rarity: str) -> str:
        return self.RARITY_COLORS.get(rarity.lower(), "gray")

    def title_block(self, title: str, subtitle: str = "") -> str:
        if subtitle:
            return f"=== {title} ===\n{subtitle}"
        return f"=== {title} ==="

    def stat_line(self, label: str, value: str) -> str:
        return f"{label}: {value}"
