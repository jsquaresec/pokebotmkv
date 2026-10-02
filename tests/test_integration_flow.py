import asyncio
import json
from datetime import datetime

from services.user_service import UserService
from services.pokemon_service import PokemonService
from services.species_service import SpeciesService
from services.party_service import PartyService
from services.queue_service import QueueService
from services.battle_service import BattleService
from services.replay_service import ReplayService
from services.ranked_service import RankedService


class DummyUser:
    def __init__(self, user_id, discord_id, username, balance=1000):
        self.id = user_id
        self.discord_id = discord_id
        self.username = username
        self.balance = balance


class DummyRankedProfile:
    def __init__(self, profile_id, owner_id, rating=1000):
        self.id = profile_id
        self.owner_id = owner_id
        self.rating = rating
        self.wins = 0
        self.losses = 0


class DummyPokemon:
    def __init__(self, mon_id, owner_id, species, level, hp, attack, defense, speed, shiny=False):
        self.id = mon_id
        self.owner_id = owner_id
        self.species = species
        self.level = level
        self.current_hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.shiny = shiny


class DummyPartySlot:
    def __init__(self, owner_id, pokemon_id, slot_index):
        self.owner_id = owner_id
        self.pokemon_id = pokemon_id
        self.slot_index = slot_index


class DummyQueueEntry:
    def __init__(self, discord_id, rating):
        self.discord_id = discord_id
        self.rating = rating
        self.created_at = datetime.utcnow()


class DummyBattle:
    def __init__(self, battle_id, battle_type, p1, p2, state_json):
        self.id = battle_id
        self.battle_type = battle_type
        self.player_one_discord_id = p1
        self.player_two_discord_id = p2
        self.state_json = state_json
        self.finished = False


class DummyReplay:
    def __init__(self, battle_id, battle_type, replay_json):
        self.battle_id = battle_id
        self.battle_type = battle_type
        self.replay_json = replay_json


class DummyUserRepo:
    def __init__(self):
        self.rows = []
        self._id = 1

    async def get_by_discord_id(self, discord_id):
        return next((x for x in self.rows if x.discord_id == discord_id), None)

    async def create(self, discord_id, username, balance=1000):
        row = DummyUser(self._id, discord_id, username, balance)
        self._id += 1
        self.rows.append(row)
        return row


class DummyRankedRepo:
    def __init__(self):
        self.rows = []
        self._id = 1

    async def get_by_owner(self, owner_id):
        return next((x for x in self.rows if x.owner_id == owner_id), None)

    async def create(self, owner_id, rating):
        row = DummyRankedProfile(self._id, owner_id, rating)
        self._id += 1
        self.rows.append(row)
        return row


class DummyPokemonRepo:
    def __init__(self):
        self.rows = []
        self._id = 1
        self.session = self

    async def add(self, pokemon):
        pokemon.id = self._id
        self._id += 1
        self.rows.append(pokemon)
        return pokemon

    async def get_by_owner(self, owner_id):
        return [x for x in self.rows if x.owner_id == owner_id]

    async def get_by_id(self, pokemon_id):
        return next((x for x in self.rows if x.id == pokemon_id), None)

    async def commit(self):
        return None


class DummyPartyRepo:
    def __init__(self):
        self.rows = []

    async def clear_party(self, owner_id):
        self.rows = [x for x in self.rows if x.owner_id != owner_id]

    async def set_slot(self, owner_id, pokemon_id, slot_index):
        slot = DummyPartySlot(owner_id, pokemon_id, slot_index)
        self.rows.append(slot)
        return slot

    async def get_party(self, owner_id):
        return sorted([x for x in self.rows if x.owner_id == owner_id], key=lambda x: x.slot_index)


class DummyQueueRepo:
    def __init__(self):
        self.rows = []

    async def get_by_discord_id(self, discord_id):
        return next((x for x in self.rows if x.discord_id == discord_id), None)

    async def enqueue(self, discord_id, rating):
        row = DummyQueueEntry(discord_id, rating)
        self.rows.append(row)
        return row

    async def list_entries(self):
        return list(self.rows)

    async def delete(self, entry):
        self.rows.remove(entry)


class DummyActiveBattleRepo:
    def __init__(self):
        self.rows = []
        self._id = 1

    async def create(self, battle_type, p1, p2, state_json):
        row = DummyBattle(self._id, battle_type, p1, p2, state_json)
        self._id += 1
        self.rows.append(row)
        return row

    async def save(self, battle, state_json, finished):
        battle.state_json = state_json
        battle.finished = finished
        return battle


class DummyReplayRepo:
    def __init__(self):
        self.rows = []

    async def create(self, battle_id, battle_type, replay_json):
        row = DummyReplay(battle_id, battle_type, replay_json)
        self.rows.append(row)
        return row


async def main():
    user_repo = DummyUserRepo()
    ranked_repo = DummyRankedRepo()
    pokemon_repo = DummyPokemonRepo()
    party_repo = DummyPartyRepo()
    queue_repo = DummyQueueRepo()
    active_battle_repo = DummyActiveBattleRepo()
    replay_repo = DummyReplayRepo()

    species_service = SpeciesService("data/species.json")
    user_service = UserService(user_repo, ranked_repo)
    pokemon_service = PokemonService(pokemon_repo, species_service)
    party_service = PartyService(party_repo, pokemon_repo)
    queue_service = QueueService(queue_repo)
    battle_service = BattleService(active_battle_repo)
    replay_service = ReplayService(replay_repo)
    ranked_service = RankedService()

    u1 = await user_service.get_or_create_user(1001, "UserOne")
    u2 = await user_service.get_or_create_user(1002, "UserTwo")
    rp1 = await ranked_repo.get_by_owner(u1.id)
    rp2 = await ranked_repo.get_by_owner(u2.id)

    p1 = await pokemon_service.create_pokemon(u1.id, "Pikachu", level=5)
    p2 = await pokemon_service.create_pokemon(u2.id, "Bulbasaur", level=5)

    await party_service.set_party(u1.id, [p1.id])
    await party_service.set_party(u2.id, [p2.id])

    result1 = await queue_service.join_or_match(u1.discord_id, rp1.rating)
    assert result1["status"] == "queued"
    result2 = await queue_service.join_or_match(u2.discord_id, rp2.rating)
    assert result2["status"] == "matched"

    battle = await battle_service.create_ranked_battle(u1.discord_id, u2.discord_id, p1, p2)
    state = battle_service.load_state(battle)

    while not state["finished"]:
        state = battle_service.apply_move(state, u1.discord_id)

    assert state["winner_discord_id"] in {u1.discord_id, u2.discord_id}

    await battle_service.save_state(battle, state)

    winner_rating, loser_rating = ranked_service.apply_result(rp1.rating, rp2.rating, 1.0)
    assert winner_rating > rp1.rating
    assert loser_rating < rp2.rating

    replay = await replay_service.save_replay(battle.id, battle.battle_type, state)
    payload = json.loads(replay.replay_json)
    assert payload["battle_id"] == battle.id
    assert len(payload["log"]) >= 1

    print("integration flow tests passed")

if __name__ == "__main__":
    asyncio.run(main())
