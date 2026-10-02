class LeaderboardService:
    def render_rows(self, rows, limit: int = 10) -> list[str]:
        out = []
        for i, row in enumerate(rows[:limit], start=1):
            out.append(f"#{i} Owner {row.owner_id} | Rating {row.rating} | W {row.wins} L {row.losses}")
        return out
