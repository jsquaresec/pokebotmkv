from repositories.queue_entries import QueueEntryRepository
from repositories.active_battles import ActiveBattleRepository
from repositories.users import UserRepository
from repositories.pokemon import PokemonRepository
from repositories.party import PartyRepository
from services.battle_service import BattleService

class MatchmakingWorkerService:
    def __init__(self, session):
        self.session = session
        self.queue_repo = QueueEntryRepository(session)
        self.active_repo = ActiveBattleRepository(session)
        self.user_repo = UserRepository(session)
        self.pokemon_repo = PokemonRepository(session)
        self.party_repo = PartyRepository(session)
        self.battle_service = BattleService(self.active_repo)

    async def _load_team(self, owner_id: int):
        slots = await self.party_repo.get_party(owner_id)
        if slots:
            team = []
            for slot in slots:
                mon = await self.pokemon_repo.get_by_id(slot.pokemon_id)
                if mon is not None:
                    team.append(mon)
            if team:
                return team
        mons = await self.pokemon_repo.get_by_owner(owner_id)
        return mons[:6]

    async def process_once(self):
        entries = await self.queue_repo.list_entries()
        if len(entries) < 2:
            return None

        entries.sort(key=lambda x: (x.rating, x.created_at))
        p1 = entries[0]
        p2 = entries[1]

        p1_user = await self.user_repo.get_by_discord_id(p1.discord_id)
        p2_user = await self.user_repo.get_by_discord_id(p2.discord_id)
        if p1_user is None or p2_user is None:
            return None

        p1_team = await self._load_team(p1_user.id)
        p2_team = await self._load_team(p2_user.id)
        if not p1_team or not p2_team:
            return None

        battle = await self.battle_service.create_ranked_battle(p1.discord_id, p2.discord_id, p1_team, p2_team)
        await self.queue_repo.delete(p1)
        await self.queue_repo.delete(p2)

        return {
            "battle_id": battle.id,
            "player_one_discord_id": p1.discord_id,
            "player_two_discord_id": p2.discord_id,
        }
