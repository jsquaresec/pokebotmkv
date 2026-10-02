from datetime import datetime, timezone
import random
from sqlalchemy import select
from models.daily_mission import DailyMission
from repositories.users import UserRepository
from repositories.inventory import InventoryRepository

TIERS = {
    'easy': {'targets': (1, 1, 1), 'rewards': [('poke_ball', 5), ('potion', 3), ('great_ball', 2)]},
    'medium': {'targets': (3, 3, 3), 'rewards': [('great_ball', 5), ('super_potion', 4), ('ultra_ball', 2), ('ether', 2)]},
    'hard': {'targets': (7, 7, 5), 'rewards': [('ultra_ball', 5), ('max_potion', 3), ('rare_candy', 2), ('ether', 5)]},
}
MISSIONS = {}
for tier, settings in TIERS.items():
    for event, target in zip(('catch', 'battle', 'shop'), settings['targets']):
        label = {'catch': f'Catch {target} Pokémon', 'battle': f'Win {target} wild battles',
                 'shop': f'Complete {target} shop purchases'}[event]
        MISSIONS[f'{event}_{tier}'] = dict(tier=tier, event=event, target=target, label=label)

class DailyMissionService:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def today(now=None):
        now = now or datetime.now(timezone.utc)
        return now.astimezone(timezone.utc).date() if now.tzinfo else now.date()

    async def board(self, uid, now=None):
        if await UserRepository(self.session).get_by_discord_id_locked(uid) is None:
            raise ValueError('Use /start first to create your trainer.')
        day = self.today(now)
        rows = list((await self.session.scalars(select(DailyMission).where(
            DailyMission.discord_id == uid, DailyMission.day == day,
            DailyMission.code.in_(MISSIONS)))).all())
        existing = {row.code for row in rows}
        for code, mission in MISSIONS.items():
            if code not in existing:
                sku, quantity = random.SystemRandom().choice(TIERS[mission['tier']]['rewards'])
                row = DailyMission(discord_id=uid, day=day, code=code, progress=0,
                                   reward_sku=sku, reward_quantity=quantity)
                self.session.add(row)
                rows.append(row)
        await self.session.flush()
        return sorted(rows, key=lambda row: list(MISSIONS).index(row.code))

    async def record(self, uid, event, now=None):
        if event not in ('catch', 'battle', 'shop'):
            raise ValueError('Unknown daily mission event.')
        for row in await self.board(uid, now):
            mission = MISSIONS[row.code]
            if mission['event'] == event:
                row.progress = min(mission['target'], row.progress + 1)
        await self.session.flush()

    async def claim(self, uid, code, day, now=None):
        if day != self.today(now):
            raise ValueError('These missions have expired. Open today’s daily missions.')
        rows = await self.board(uid, now)
        row = next((r for r in rows if r.code == code), None)
        if row is None or row.progress < MISSIONS[code]['target']:
            raise ValueError('Complete this mission first.')
        if row.claimed_at is not None:
            raise ValueError('This mission reward has already been claimed.')
        item = await InventoryRepository(self.session).get_item_locked(uid, row.reward_sku)
        if item is None:
            await InventoryRepository(self.session).add_item(uid, row.reward_sku, row.reward_quantity)
        else:
            item.quantity += row.reward_quantity
        row.claimed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.flush()
        return row
