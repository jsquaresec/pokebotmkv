from sqlalchemy import select
from models.party import PartySlot


async def ensure_not_in_party(session, pokemon_id):
    slot = (await session.execute(select(PartySlot.id).where(PartySlot.pokemon_id == pokemon_id).limit(1))).scalar_one_or_none()
    if slot is not None:
        raise ValueError("Remove this Pokémon from its party before transferring or listing it.")
