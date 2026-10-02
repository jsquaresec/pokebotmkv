"""Upgrade old fallback Pokémon without reviving them or refilling spent PP."""
import json
import math

from sqlalchemy import select
from models.pokemon import PokemonInstance
from services.content_registry_v70 import ContentRegistryV70
from services.moveset_v80_service import MovesetV80Service


class CatalogUpgradeService:
    REVISION = 1

    def __init__(self, registry=None):
        self.registry = registry or ContentRegistryV70()

    def upgrade(self, mon):
        if (getattr(mon, 'catalog_revision', 0) or 0) >= self.REVISION:
            return False
        data = self.registry.species(mon.species)
        if data is None:
            return False
        ratio = max(0, min(1, mon.current_hp / max(1, mon.max_hp)))
        mon.dex_number = data['dex_number']
        mon.max_hp = data['base_hp'] + mon.level * 2
        mon.current_hp = min(mon.max_hp, math.ceil(mon.max_hp * ratio))
        for stat in ('attack', 'defense', 'speed'):
            setattr(mon, stat, data['base_' + stat] + mon.level)
        mon.primary_type = data['types'][0]
        mon.secondary_type = data['types'][1] if len(data['types']) > 1 else None
        if mon.ability not in [a['name'] for a in data['abilities']]:
            mon.ability = next((a['name'] for a in data['abilities'] if not a['hidden']), data['abilities'][0]['name'])
        if data['gender_rate'] in (-1, 0, 8):
            mon.gender = {-1:'genderless', 0:'male', 8:'female'}[data['gender_rate']]
        movesets = MovesetV80Service()
        old = movesets.load(mon)
        legal = set()
        current = data
        # Keep legitimate moves inherited from earlier evolutionary stages.
        while current:
            legal.update(self.registry.legal_moves(current['name'], mon.level, supported_only=False))
            current = self.registry.species(current['evolves_from']) if current.get('evolves_from') else None
        kept = []
        for slot in old:
            if slot['name'] not in legal or slot['name'] in [s['name'] for s in kept]:
                continue
            new = movesets._slot(slot['name'], self.registry)
            spent = max(0, slot.get('max_pp', new['max_pp']) - slot['pp'])
            new['pp'] = max(0, new['max_pp'] - spent) if slot['pp'] > 0 else 0
            kept.append(new)
        if not kept:
            kept = [movesets._slot(name, self.registry) for name in self.registry.legal_moves(mon.species, mon.level)[-4:]]
            # Replacing an old fallback moveset must not grant a free PP refill.
            if old:
                fraction = sum(s['pp'] for s in old) / max(1, sum(s['max_pp'] for s in old))
                for slot in kept:
                    slot['pp'] = max(0, min(slot['max_pp'], math.floor(slot['max_pp'] * fraction)))
        mon.moves_json = json.dumps(kept[:4])
        mon.catalog_revision = self.REVISION
        return True

    async def upgrade_available(self, session):
        count, last_id = 0, 0
        while True:
            mons = (await session.execute(select(PokemonInstance).where(
                PokemonInstance.catalog_revision < self.REVISION, PokemonInstance.locked.is_(False),
                PokemonInstance.id > last_id).order_by(PokemonInstance.id).limit(200).with_for_update())).scalars().all()
            if not mons:
                break
            for mon in mons:
                count += self.upgrade(mon)
                last_id = mon.id
            await session.flush()
        return count
