import json
from sqlalchemy import select
from models.idempotency_key import IdempotencyKey


class IdempotencyService:
    def __init__(self, session):
        self.session = session

    async def acquire(self, scope: str, request_key: str, actor_discord_id: int):
        existing = (
            await self.session.execute(
                select(IdempotencyKey).where(IdempotencyKey.scope == scope, IdempotencyKey.request_key == request_key)
            )
        ).scalar_one_or_none()
        if existing:
            raise ValueError("This request has already been processed.")
        row = IdempotencyKey(scope=scope, request_key=request_key, actor_discord_id=actor_discord_id)
        self.session.add(row)
        await self.session.flush()
        return row

    async def complete(self, row, result: dict):
        row.result_json = json.dumps(result, separators=(",", ":"), default=str)
        await self.session.flush()
