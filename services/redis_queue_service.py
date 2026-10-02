import json
from config import settings

class RedisQueueService:
    def __init__(self):
        self._client = None
        try:
            import redis.asyncio as redis
            self._client = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            self._client = None

    async def push(self, queue_name: str, payload: dict) -> bool:
        if self._client is None:
            return False
        await self._client.rpush(queue_name, json.dumps(payload))
        return True

    async def pop(self, queue_name: str):
        if self._client is None:
            return None
        raw = await self._client.lpop(queue_name)
        if raw is None:
            return None
        return json.loads(raw)

    async def length(self, queue_name: str) -> int:
        if self._client is None:
            return 0
        return int(await self._client.llen(queue_name))

    async def peek_recent(self, queue_name: str, limit: int = 20) -> list[dict]:
        if self._client is None:
            return []
        rows = await self._client.lrange(queue_name, max(0, -limit), -1)
        out = []
        for row in rows:
            try:
                out.append(json.loads(row))
            except Exception:
                out.append({"raw": row})
        return out
