import asyncio
import json
from datetime import datetime
from services.matchmaking_worker_service import MatchmakingWorkerService

class DummyEntry:
    def __init__(self, discord_id, rating):
        self.discord_id = discord_id
        self.rating = rating
        self.created_at = datetime.utcnow()

class DummyUser:
    def __init__(self, user_id, discord_id):
        self.id = user_id
        self.discord_id = discord_id

class DummyMon:
    def __init__(self, mon_id, owner_id, species):
        self.id = mon_id
        self.owner_id = owner_id
        self.species = species
        self.current_hp = 20
        self.max_hp = 20
        self.attack = 10
        self.defense = 10
        self.speed = 10

class DummyBattle:
    def __init__(self, battle_id, battle_type, p1, p2, state_json):
        self.id = battle_id
        self.battle_type = battle_type
        self.player_one_discord_id = p1
        self.player_two_discord_id = p2
        self.state_json = state_json
        self.finished = False

class DummyQueueRepo:
    def __init__(self):
        self.entries = [DummyEntry(1001, 1000), DummyEntry(1002, 1010)]
    async def list_entries(self):
        return list(self.entries)
    async def delete(self, entry):
        self.entries.remove(entry)

class DummyUserRepo:
    async def get_by_discord_id(self, discord_id):
        mapping = {1001: DummyUser(1, 1001), 1002: DummyUser(2, 1002)}
        return mapping.get(discord_id)

class DummyPokemonRepo:
    async def get_by_id(self, pokemon_id):
        mapping = {1: DummyMon(1, 1, "Pikachu"), 2: DummyMon(2, 2, "Bulbasaur")}
        return mapping.get(pokemon_id)
    async def get_by_owner(self, owner_id):
        if owner_id == 1:
            return [DummyMon(1, 1, "Pikachu")]
        if owner_id == 2:
            return [DummyMon(2, 2, "Bulbasaur")]
        return []

class DummyPartySlot:
    def __init__(self, pokemon_id):
        self.pokemon_id = pokemon_id

class DummyPartyRepo:
    async def get_party(self, owner_id):
        if owner_id == 1:
            return [DummyPartySlot(1)]
        if owner_id == 2:
            return [DummyPartySlot(2)]
        return []

class DummyActiveBattleRepo:
    def __init__(self):
        self.next_id = 1
    async def create(self, battle_type, p1, p2, state_json):
        row = DummyBattle(self.next_id, battle_type, p1, p2, state_json)
        self.next_id += 1
        return row

class DummySession:
    pass

async def main():
    session = DummySession()
    service = MatchmakingWorkerService.__new__(MatchmakingWorkerService)
    service.session = session
    service.queue_repo = DummyQueueRepo()
    service.active_repo = DummyActiveBattleRepo()
    service.user_repo = DummyUserRepo()
    service.pokemon_repo = DummyPokemonRepo()
    service.party_repo = DummyPartyRepo()
    from services.battle_service import BattleService
    service.battle_service = BattleService(service.active_repo)

    result = await service.process_once()
    assert result is not None
    assert result["battle_id"] == 1
    assert set([result["player_one_discord_id"], result["player_two_discord_id"]]) == {1001, 1002}
    print("matchmaking worker service tests passed")

if __name__ == "__main__":
    asyncio.run(main())
