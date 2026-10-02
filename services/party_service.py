from repositories.party import PartyRepository
from repositories.pokemon import PokemonRepository

class PartyService:
    def __init__(self, party_repo: PartyRepository, pokemon_repo: PokemonRepository):
        self.party_repo = party_repo
        self.pokemon_repo = pokemon_repo

    async def set_party(self, owner_id: int, pokemon_ids: list[int]) -> None:
        if len(pokemon_ids) > 6:
            raise ValueError("Party cannot exceed 6 Pokémon.")
        if len(set(pokemon_ids)) != len(pokemon_ids):
            raise ValueError("Party cannot contain duplicate Pokémon IDs.")

        for pokemon_id in pokemon_ids:
            pokemon = await self.pokemon_repo.get_by_id(pokemon_id)
            if pokemon is None or pokemon.owner_id != owner_id or getattr(pokemon, "locked", False):
                raise ValueError(f"Pokémon #{pokemon_id} is unavailable.")
        await self.party_repo.clear_party(owner_id)
        for i, pokemon_id in enumerate(pokemon_ids, start=1):
            pokemon = await self.pokemon_repo.get_by_id(pokemon_id)
            if pokemon is None or pokemon.owner_id != owner_id:
                raise ValueError(f"Pokémon #{pokemon_id} is not yours.")
            await self.party_repo.set_slot(owner_id, pokemon_id, i)
