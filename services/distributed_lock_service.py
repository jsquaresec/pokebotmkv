class DistributedLockService:
    async def acquire(self, key: str) -> str:
        return "local-token"

    async def release(self, key: str, token: str) -> None:
        return None
