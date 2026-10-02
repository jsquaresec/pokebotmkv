import json
from repositories.notification_deliveries import NotificationDeliveryRepository

class NotificationService:
    def __init__(self, repo: NotificationDeliveryRepository):
        self.repo = repo

    async def record_match_created(self, recipient_discord_id: int, battle_id: int, payload: dict):
        return await self.repo.create(
            event_type="ranked_match_created",
            recipient_discord_id=recipient_discord_id,
            related_battle_id=battle_id,
            status="queued",
            payload_json=json.dumps(payload),
            retry_count=0,
        )

    async def recent_for_recipient(self, recipient_discord_id: int, limit: int = 25):
        return await self.repo.latest_for_recipient(recipient_discord_id, limit)

    async def recent_all(self, limit: int = 50):
        return await self.repo.latest_all(limit)

    async def stats(self):
        return await self.repo.stats()
