from config import settings

class RankedService:
    def expected_score(self, rating_a: int, rating_b: int) -> float:
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def apply_result(self, rating_a: int, rating_b: int, score_a: float) -> tuple[int, int]:
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = self.expected_score(rating_b, rating_a)
        new_a = round(rating_a + settings.ranked_k_factor * (score_a - expected_a))
        new_b = round(rating_b + settings.ranked_k_factor * ((1 - score_a) - expected_b))
        return new_a, new_b
