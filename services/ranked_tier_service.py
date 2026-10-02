class RankedTierService:
    def tier_for_rating(self, rating: int) -> str:
        if rating >= 1600:
            return "Elite"
        if rating >= 1400:
            return "Gold"
        if rating >= 1200:
            return "Silver"
        return "Bronze"
