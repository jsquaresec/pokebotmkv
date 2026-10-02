from datetime import datetime
from sqlalchemy import func, select
from models.pokedex_entry import PokedexEntry


class PokedexRepository:
    def __init__(self, session):
        self.session = session

    async def record(self, discord_id: int, species: str, caught: bool = False):
        stmt = (
            select(PokedexEntry)
            .where(PokedexEntry.discord_id == discord_id, PokedexEntry.species == species)
            .with_for_update()
        )
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = PokedexEntry(discord_id=discord_id, species=species, seen_count=0, caught_count=0)
            self.session.add(row)
        row.seen_count += 1
        if caught:
            row.caught_count += 1
            row.first_caught_at = row.first_caught_at or datetime.utcnow()
        await self.session.flush()
        return row

    async def summary(self, discord_id: int):
        stmt = select(func.count(PokedexEntry.id), func.sum(PokedexEntry.caught_count)).where(
            PokedexEntry.discord_id == discord_id
        )
        seen, catches = (await self.session.execute(stmt)).one()
        return {"species_seen": seen or 0, "total_catches": catches or 0}
