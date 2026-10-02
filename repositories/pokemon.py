from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.pokemon import PokemonInstance

class PokemonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, pokemon: PokemonInstance) -> PokemonInstance:
        self.session.add(pokemon)
        await self.session.commit()
        await self.session.refresh(pokemon)
        return pokemon

    async def get_by_owner(self, owner_id: int) -> list[PokemonInstance]:
        result = await self.session.execute(select(PokemonInstance).where(PokemonInstance.owner_id == owner_id))
        return list(result.scalars().all())

    async def get_by_id(self, pokemon_id: int) -> PokemonInstance | None:
        result = await self.session.execute(select(PokemonInstance).where(PokemonInstance.id == pokemon_id))
        return result.scalar_one_or_none()

    async def get_by_id_locked(self, pokemon_id: int) -> PokemonInstance | None:
        result = await self.session.execute(select(PokemonInstance).where(PokemonInstance.id == pokemon_id).with_for_update())
        return result.scalar_one_or_none()

    async def search(self, owner_id: int, species: str | None = None, shiny: bool | None = None, favorite: bool | None = None, min_iv: float = 0, limit: int = 20, page: int = 1):
        if page < 1 or not 0 <= min_iv <= 100:
            raise ValueError("Page must be positive and IV between 0 and 100.")
        stmt = select(PokemonInstance).where(PokemonInstance.owner_id == owner_id, PokemonInstance.locked.is_(False))
        if species:
            stmt = stmt.where(PokemonInstance.species.ilike(f"%{species}%"))
        if shiny is not None:
            stmt = stmt.where(PokemonInstance.shiny.is_(shiny))
        if favorite is not None:
            stmt = stmt.where(PokemonInstance.favorite.is_(favorite))
        total_iv = PokemonInstance.iv_hp + PokemonInstance.iv_attack + PokemonInstance.iv_defense + PokemonInstance.iv_speed
        stmt = stmt.where(total_iv * 100.0 / 124 >= min_iv)
        size = min(max(limit, 1), 50)
        return list((await self.session.execute(stmt.order_by(PokemonInstance.id.desc()).offset((page-1)*size).limit(size))).scalars().all())
