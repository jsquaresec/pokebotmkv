import json
from datetime import datetime

from sqlalchemy import or_, select

from battle.wild_engine import WildTurnEngine
from models.active_battle import ActiveBattle
from models.pokemon import PokemonInstance
from models.queue_entry import QueueEntry
from models.wild_encounter import WildEncounter
from repositories.inventory import InventoryRepository
from repositories.party import PartyRepository
from repositories.users import UserRepository
from services.content_registry_v70 import ContentRegistryV70
from services.encounter_v70_service import EncounterV70Service
from services.moveset_v80_service import MovesetV80Service
from services.progression_v70_service import ProgressionV70Service


WILD_WIN_GOLD_REWARD = 250


def battle_states(row):
    raw = json.loads(row.battle_state_json or "{}")
    if "battles" in raw:
        return raw["battles"]
    if raw.get("owner") is not None:
        return {str(raw["owner"]): raw}
    return {}


def load_battle(row, uid=None):
    battles = battle_states(row)
    if uid is not None:
        return battles.get(str(uid), {})
    return next(iter(battles.values()), {}) if len(battles) == 1 else {}


def save_battle(row, uid, state):
    battles = battle_states(row)
    battles[str(uid)] = state
    row.battle_state_json = json.dumps({"battles": battles})


class WildBattleService:
    def __init__(self, session, registry=None, rng=None):
        self.session = session
        self.registry = registry or ContentRegistryV70()
        self.engine = WildTurnEngine(self.registry, rng)

    def snapshot(self, mon):
        data = self.registry.species(mon.species) or {}
        if not MovesetV80Service.load(mon):
            MovesetV80Service().initialize(mon, self.registry)
        return {"id": mon.id, "name": mon.species, "level": mon.level,
                "shiny": mon.shiny,
                "hp": mon.current_hp, "max_hp": mon.max_hp, "attack": mon.attack,
                "defense": mon.defense, "speed": mon.speed,
                "special_attack": data.get("base_special_attack", data.get("base_attack", 10)) + mon.level,
                "special_defense": data.get("base_special_defense", data.get("base_defense", 10)) + mon.level,
                "types": [t for t in (mon.primary_type, mon.secondary_type) if t],
                "stages": {}, "status": None, "moves": MovesetV80Service.load(mon)}

    async def start(self, row, uid):
        state = load_battle(row, uid)
        if state and not state.get("finished"):
            return state
        user = await UserRepository(self.session).get_by_discord_id_locked(uid)
        if not user:
            raise ValueError("Use /start and set your party first.")
        current_rows = (await self.session.execute(select(WildEncounter).where(
            WildEncounter.status == "open"))).scalars().all()
        if any((s := load_battle(encounter, uid)) and not s.get("finished") and encounter.id != row.id
               for encounter in current_rows):
            raise ValueError("Finish your current wild battle before starting another.")
        active = (await self.session.execute(select(ActiveBattle.id).where(
            ActiveBattle.finished.is_(False), or_(ActiveBattle.player_one_discord_id == uid,
                                                ActiveBattle.player_two_discord_id == uid)).limit(1))).scalar_one_or_none()
        queued = (await self.session.execute(select(QueueEntry.id).where(QueueEntry.discord_id == uid))).scalar_one_or_none()
        if active is not None or queued is not None:
            raise ValueError("Finish your ranked battle or queue before starting a wild battle.")
        party_repo = PartyRepository(self.session)
        slots = await party_repo.get_party(user.id)
        if not slots:
            # Battle is a GUI action, so do not dead-end the player on a slash
            # command prerequisite. Seed an empty party with their first usable
            # Pokémon and immediately continue into the battle GUI.
            first_mon = (await self.session.execute(
                select(PokemonInstance).where(
                    PokemonInstance.owner_id == user.id,
                    PokemonInstance.locked.is_(False),
                ).order_by(PokemonInstance.id.asc()).limit(1)
            )).scalar_one_or_none()
            if first_mon is None:
                raise ValueError("You have no available Pokémon. Catch one or choose a starter first.")
            await party_repo.replace_party(user.id, [first_mon.id])
            slots = await party_repo.get_party(user.id)
        # Lock in ID order, preserving the user's party order in the snapshots.
        mons = {}
        for pid in sorted(slot.pokemon_id for slot in slots):
            mon = (await self.session.execute(select(PokemonInstance).where(PokemonInstance.id == pid).with_for_update())).scalar_one_or_none()
            if not mon or mon.owner_id != user.id or mon.locked:
                raise ValueError("Your party is unavailable or already battling.")
            from services.catalog_upgrade_service import CatalogUpgradeService
            CatalogUpgradeService(self.registry).upgrade(mon)
            mons[pid] = mon
        team = [self.snapshot(mons[slot.pokemon_id]) for slot in slots]
        living = [i for i, mon in enumerate(team) if mon["hp"] > 0]
        if not living:
            raise ValueError("Your entire party has fainted. Heal your Pokémon first.")
        for mon in mons.values():
            mon.locked = True
        data = self.registry.species(row.species)
        moves = self.registry.legal_moves(row.species, row.level)[-4:]
        wild = {"name": row.species, "level": row.level, "hp": row.current_hp, "max_hp": row.max_hp,
                "attack": data["base_attack"] + row.level, "defense": data["base_defense"] + row.level,
                "speed": data["base_speed"] + row.level,
                "special_attack": data.get("base_special_attack", data["base_attack"]) + row.level,
                "special_defense": data.get("base_special_defense", data["base_defense"]) + row.level,
                "types": data["types"], "stages": {}, "status": None,
                "moves": [MovesetV80Service._slot(name, self.registry) for name in moves]}
        state = {"owner": uid, "owner_id": user.id, "team": team, "active": living[0], "wild": wild,
                 "turn": 1, "finished": False, "log": [f'Go, {team[living[0]]["name"]}!']}
        save_battle(row, uid, state)
        return state

    async def apply(self, encounter_id, channel_id, uid, kind, value=None, expected_turn=None):
        row = (await self.session.execute(select(WildEncounter).where(
            WildEncounter.id == encounter_id, WildEncounter.channel_id == channel_id).with_for_update())).scalar_one_or_none()
        if not row or row.status != "open" or row.expires_at <= datetime.utcnow():
            raise ValueError("This encounter has ended. Open the newest spawn.")
        if kind == "start":
            await self.start(row, uid)
            await self.session.flush()
            return row
        state = load_battle(row, uid)
        if not state or state.get("finished"):
            raise ValueError("Only the trainer battling this Pokémon can take a turn.")
        if expected_turn is not None and state["turn"] != expected_turn:
            return row  # Re-render stale controls without spending PP or balls.
        active, wild = state["team"][state["active"]], state["wild"]
        for member in [*state['team'], wild]:
            member.pop('flinch', None)
            member['physical_damage_taken'] = 0
            member['special_damage_taken'] = 0
        if active["hp"] <= 0 and kind not in ("switch", "run"):
            raise ValueError("Choose a healthy party Pokémon to replace your fainted Pokémon.")
        state["log"] = []
        if kind == "move":
            self.engine.turn(active, wild, value, state["log"])
        elif kind == "switch":
            index = int(value)
            if not 0 <= index < len(state["team"]) or index == state["active"] or state["team"][index]["hp"] <= 0:
                raise ValueError("Choose another healthy party Pokémon.")
            forced = active["hp"] <= 0
            active["stages"] = {}
            state["active"] = index
            active = state["team"][index]
            active["stages"] = {}
            state["log"].append(f'Go, {active["name"]}!')
            if not forced:
                self.engine.use(wild, active, self.engine.enemy_move(wild), state["log"])
                self.engine.residual(active, wild, state["log"])
        elif kind == "ball":
            row.status_effect = wild.get("status")
            mon = await EncounterV70Service(self.session, self.registry, self.engine.rng).attempt_catch(
                channel_id, uid, value, UserRepository(self.session), InventoryRepository(self.session),
                encounter_id=encounter_id, battle_turn=True, battle_state=state)
            if mon:
                state["finished"] = True
                state["result"] = "caught"
                state["log"].append(f'Caught {mon.species}! +500 gold.')
            else:
                state["log"].append("The Pokémon broke free!")
                self.engine.use(wild, active, self.engine.enemy_move(wild), state["log"])
                self.engine.residual(active, wild, state["log"])
        elif kind == "run":
            state["finished"] = True
            state["result"] = "ran"
            state["log"].append("You escaped from the wild Pokémon.")
            # Running ends only this trainer's private battle.
        else:
            raise ValueError("Unknown battle action.")
        if not state["finished"]:
            if active.get('escaped') or wild.get('escaped'):
                state['finished'], state['result'] = True, 'ran'
            elif wild["hp"] <= 0:
                state["finished"], state["result"] = True, "won"
                state["log"].append("The wild Pokémon fainted. It can no longer be caught.")
                user = await UserRepository(self.session).get_by_discord_id_locked(uid)
                if user is None or user.id != state['owner_id']:
                    raise ValueError("The battling trainer is unavailable.")
                user.balance += WILD_WIN_GOLD_REWARD
                from services.daily_mission_service import DailyMissionService
                await DailyMissionService(self.session).record(uid, 'battle')
                state['gold_reward'] = WILD_WIN_GOLD_REWARD
                state['gold_balance'] = user.balance
                state['log'].append(f'You earned {WILD_WIN_GOLD_REWARD} gold!')
            elif not any(mon["hp"] > 0 for mon in state["team"]):
                state["finished"], state["result"] = True, "lost"
                state["log"].append("Your entire party fainted. Heal up before trying again.")
            elif active["hp"] <= 0:
                state["log"].append("Choose another party Pokémon to continue.")
        # Wild HP is private to this trainer's battle.
        for entry in sorted(state["team"], key=lambda m: m["id"]):
            mon = (await self.session.execute(select(PokemonInstance).where(PokemonInstance.id == entry["id"]).with_for_update())).scalar_one()
            if mon.owner_id != state["owner_id"]:
                raise ValueError("Party ownership changed; this turn cannot be applied.")
            mon.current_hp = entry["hp"]
            mon.moves_json = json.dumps(entry["moves"])
            if state["finished"]:
                mon.locked = False
                from services.catalog_upgrade_service import CatalogUpgradeService
                CatalogUpgradeService(self.registry).upgrade(mon)
            if state.get("result") == "won" and entry["id"] == active["id"] and mon.current_hp > 0:
                mon.experience = max(mon.experience, mon.level ** 3)
                xp = row.level * 20
                ProgressionV70Service().grant_experience(mon, xp, self.registry)
                state["log"].append(f'{mon.species} earned {xp} XP!')
                entry["level"], entry["hp"], entry["max_hp"] = mon.level, mon.current_hp, mon.max_hp
        state["turn"] += 1
        save_battle(row, uid, state)
        await self.session.flush()
        return row

    @staticmethod
    async def expire(session):
        rows = (await session.execute(select(WildEncounter).where(
            WildEncounter.status == "open", WildEncounter.expires_at <= datetime.utcnow()).with_for_update())).scalars().all()
        for row in rows:
            battles = battle_states(row)
            for uid, state in battles.items():
                if state and not state.get("finished"):
                    for entry in sorted(state["team"], key=lambda m: m["id"]):
                        mon = (await session.execute(select(PokemonInstance).where(PokemonInstance.id == entry["id"]).with_for_update())).scalar_one_or_none()
                        if mon and mon.owner_id == state["owner_id"]:
                            mon.locked = False
                            from services.catalog_upgrade_service import CatalogUpgradeService
                            CatalogUpgradeService().upgrade(mon)
                    state["finished"], state["result"] = True, "expired"
                    state["log"] = ["The wild Pokémon fled."]
                    battles[uid] = state
            row.battle_state_json = json.dumps({"battles": battles})
            row.status = "expired"
        await session.flush()

