class OnboardingGuideService:
    def quick_start(self) -> str:
        return (
            "1. Use /start or /start_game\n"
            "2. Catch a Pokémon\n"
            "3. View your profile\n"
            "4. Try a battle\n"
            "5. Visit the shop and market"
        )

    def beginner_tips(self) -> list[str]:
        return [
            "Catch multiple Pokémon before ranked play.",
            "Use healing items before long battle sessions.",
            "Check your profile and inventory often.",
            "Give feedback when something feels confusing.",
        ]
