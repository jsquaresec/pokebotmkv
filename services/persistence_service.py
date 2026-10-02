from repositories.pokemon import PokemonRepository

class PersistenceService:
    def __init__(self, pokemon_repo: PokemonRepository):
        self.pokemon_repo = pokemon_repo

    async def sync_battle_hp(self, state: dict) -> None:
        for side_key in ("player_one", "player_two"):
            side = state[side_key]
            mon = await self.pokemon_repo.get_by_id(side["pokemon_id"])
            if mon is not None:
                mon.current_hp = side["hp"]
        await self.pokemon_repo.session.commit()
