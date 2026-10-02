from services.redis_queue_service import RedisQueueService

class BattleEventService:
    def __init__(self, redis_queue: RedisQueueService | None = None):
        self.redis_queue = redis_queue or RedisQueueService()

    async def publish_match_created(self, battle_id: int, p1_discord_id: int, p2_discord_id: int) -> bool:
        return await self.redis_queue.push("battle_events", {
            "type": "ranked_match_created",
            "battle_id": battle_id,
            "player_one_discord_id": p1_discord_id,
            "player_two_discord_id": p2_discord_id,
        })

    async def recent_events(self, limit: int = 20) -> list[dict]:
        return await self.redis_queue.peek_recent("battle_events", limit)
