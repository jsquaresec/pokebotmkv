class EmbedFactory:
    def catch_card(self, species: str, rarity: str, level: int, rewards: dict, hints: list[str]) -> str:
        rarity_text = f"{rarity.upper()}"
        reward_lines = "\n".join([f"• {k}: {v}" for k, v in rewards.items()])
        hint_lines = "\n".join([f"➡ {h}" for h in hints])
        return (
            f"[{rarity_text} CATCH]\n\n"
            f"{species} Lv.{level}\n\n"
            f"Rewards:\n{reward_lines}\n\n"
            f"Next steps:\n{hint_lines}"
        )

    def spawn_card(self, species: str, rarity: str, level: int) -> str:
        return (
            f"🌿 A wild Pokémon appeared!\n\n"
            f"{rarity.upper()} — {species}\n"
            f"Level: {level}\n\n"
            f"Use /catch {species.lower()}"
        )
