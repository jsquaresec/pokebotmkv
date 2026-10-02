from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.party import PartySlot

class PartyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_party(self, owner_id: int) -> list[PartySlot]:
        result = await self.session.execute(
            select(PartySlot).where(PartySlot.owner_id == owner_id).order_by(PartySlot.slot_index.asc())
        )
        return list(result.scalars().all())

    async def replace_party(self, owner_id: int, pokemon_ids: list[int]) -> None:
        """Replace all slots in the caller's transaction; never commit partially."""
        await self.session.execute(delete(PartySlot).where(PartySlot.owner_id == owner_id))
        self.session.add_all([
            PartySlot(owner_id=owner_id, pokemon_id=pid, slot_index=index)
            for index, pid in enumerate(pokemon_ids, 1)
        ])
        await self.session.flush()

    async def clear_party(self, owner_id: int) -> None:
        await self.session.execute(delete(PartySlot).where(PartySlot.owner_id == owner_id))
        await self.session.commit()

    async def set_slot(self, owner_id: int, pokemon_id: int, slot_index: int) -> PartySlot:
        slot = PartySlot(owner_id=owner_id, pokemon_id=pokemon_id, slot_index=slot_index)
        self.session.add(slot)
        await self.session.commit()
        await self.session.refresh(slot)
        return slot
