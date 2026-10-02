class ContentRotationAnnouncementService:
    def rotation_message(self, rotation_key: str, species_list: list[str]) -> str:
        names = ", ".join(species_list[:10])
        if len(species_list) > 10:
            names += ", ..."
        return f"🔄 Rotation active: **{rotation_key}**\nFeatured Pokémon: {names}"

    def variant_message(self, display_name: str) -> str:
        return f"✨ Special encounter available: **{display_name}**"
