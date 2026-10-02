from sqlalchemy import or_, select

from models.active_battle import ActiveBattle
from models.queue_entry import QueueEntry
from repositories.users import UserRepository
from repositories.party import PartyRepository
from repositories.pokemon import PokemonRepository
from services.content_registry_v70 import ContentRegistryV70
from services.moveset_v80_service import MovesetV80Service


class PokemonCenterService:
    COST = 500

    def __init__(self, session):
        self.session = session

    async def heal_party(self, discord_id):
        """Caller owns the transaction; payment and healing commit together."""
        user = await UserRepository(self.session).get_by_discord_id_locked(discord_id)
        if user is None:
            raise ValueError("Use /start first.")
        slots = await PartyRepository(self.session).get_party(user.id)
        if not slots:
            raise ValueError("Your party is empty. Use /party_set first.")
        active = (await self.session.execute(select(ActiveBattle.id).where(
            ActiveBattle.finished.is_(False), or_(ActiveBattle.player_one_discord_id == discord_id,
                                                ActiveBattle.player_two_discord_id == discord_id)).limit(1))).scalar_one_or_none()
        queued = (await self.session.execute(select(QueueEntry.id).where(
            QueueEntry.discord_id == discord_id))).scalar_one_or_none()
        if active is not None or queued is not None:
            raise ValueError("Finish your battle or leave the ranked queue before healing.")
        mons = []
        for pid in sorted(slot.pokemon_id for slot in slots):
            mon = await PokemonRepository(self.session).get_by_id_locked(pid)
            if mon is None or mon.owner_id != user.id or mon.locked:
                raise ValueError("Your party is busy. Finish your battle before healing.")
            mons.append(mon)
        movesets = MovesetV80Service()
        if all(mon.current_hp == mon.max_hp and
               all(move['pp'] == move['max_pp'] for move in movesets.load(mon)) for mon in mons):
            raise ValueError("Your party already has full HP and PP. No gold was charged.")
        if user.balance < self.COST:
            raise ValueError(f"Healing costs {self.COST:,} gold. You have {user.balance:,} gold. No gold was charged.")
        for mon in mons:
            mon.current_hp = mon.max_hp
            if not movesets.load(mon):
                movesets.initialize(mon, ContentRegistryV70())
            movesets.restore_pp(mon)
        user.balance -= self.COST
        await self.session.flush()
        return len(mons), user.balance
