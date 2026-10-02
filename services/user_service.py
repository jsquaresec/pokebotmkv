from config import settings
from repositories.users import UserRepository
from repositories.ranked_profiles import RankedProfileRepository

class UserService:
    def __init__(self, user_repo: UserRepository, ranked_repo: RankedProfileRepository | None = None):
        self.user_repo = user_repo
        self.ranked_repo = ranked_repo

    async def get_or_create_user(self, discord_id: int, username: str):
        user = await self.user_repo.get_by_discord_id(discord_id)
        if user:
            return user
        user = await self.user_repo.create(discord_id=discord_id, username=username, balance=1000)
        if self.ranked_repo is not None:
            existing = await self.ranked_repo.get_by_owner(user.id)
            if existing is None:
                await self.ranked_repo.create(user.id, settings.ranked_start_rating)
        return user
