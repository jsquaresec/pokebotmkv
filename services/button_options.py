"""Read-only choices for command inputs. Handlers revalidate before mutation."""
from datetime import datetime, timedelta

import discord


async def options_for(interaction, command, parameter, values):
    """Return (label/value pairs, allow_custom). IDs always come from records."""
    name, action = parameter.name, command.name
    if parameter.choices:
        return [(choice.name, choice.value) for choice in parameter.choices], False
    if parameter.type == discord.AppCommandOptionType.boolean:
        return [("Yes", True), ("No", False)], False
    if name == "species":
        from services.content_registry_v70 import ContentRegistryV70
        return [(s, s) for s in ContentRegistryV70().all_species()], True
    if action in ("guild_join", "guild_leave") and name == "name":
        from cogs.guild import _GUILD
        rows = [(n, n) for n, guild in _GUILD.guilds.items()
                if (interaction.user.id in guild["members"]) == (action == "guild_leave")]
        return rows, False
    if name in ("start_iso", "end_iso"):
        now = datetime.utcnow().replace(microsecond=0)
        if name == "end_iso" and values.get("start_iso"):
            now = datetime.fromisoformat(values["start_iso"])
        offsets = [("Now (UTC)", 0), ("In 1 hour", 1), ("In 6 hours", 6), ("In 24 hours", 24)]
        if name == "end_iso":
            offsets = [("1 hour after start", 1), ("6 hours after start", 6), ("1 day after start", 24), ("1 week after start", 168)]
        return [(label, (now + timedelta(hours=hours)).isoformat()) for label, hours in offsets], True
    entity_names = {"pokemon_id", "listing_id", "auction_id", "offer_id", "request_id", "battle_id",
                    "user", "user_id", "to_discord_id", "tier"}
    if name in entity_names or (action == "auction_bid" and name == "amount"):
        return await record_options(interaction, action, name, values), False if name in entity_names else True
    if parameter.type in (discord.AppCommandOptionType.integer, discord.AppCommandOptionType.number):
        presets = (1, 5, 10, 25, 50, 100)
        if name in ("price", "starting_bid", "bid_increment", "max_price", "amount"):
            presets = (1, 5, 10, 25, 100, 500, 1000, 2500, 5000, 10000)
        elif name == "hours":
            presets = (1, 6, 12, 24, 48, 168)
        elif name == "min_iv":
            presets = (0, 25, 50, 75, 90, 100)
        elif name == "page":
            presets = (1, 2, 3, 4, 5, 10)
        if name == "bid_increment" and "starting_bid" in values:
            presets = tuple(n for n in presets if n <= values["starting_bid"]) or (1,)
        presets = [n for n in presets if (parameter.min_value is None or n >= parameter.min_value)
                   and (parameter.max_value is None or n <= parameter.max_value)]
        return [(f"{n:,}", n) for n in presets], True
    if name == "bio":
        return [("Pokémon collector", "Pokémon collector"), ("Battle enthusiast", "Battle enthusiast"),
                ("Shiny hunter", "Shiny hunter")], True
    if name == "code":
        return [("Community event", "community_event"), ("Catch challenge", "catch_challenge")], True
    if name == "event_type":
        return [(label, value) for label, value in (("Catch", "catch"), ("Battle", "battle"), ("Shop", "shop"))], True
    return [], True


async def record_options(interaction, action, name, values):
    from sqlalchemy import select
    from core.database import SessionLocal
    from models.user import User
    from models.pokemon import PokemonInstance
    from models.party import PartySlot
    from models.market_listing import MarketListing
    from models.auction import Auction
    from models.trade_offer import TradeOffer
    from models.friendship import Friendship
    from models.active_battle import ActiveBattle
    from models.battle_replay import BattleReplay
    from models.season_reward_claim import SeasonRewardClaim
    from services.season_pass_service import SeasonPassService, REWARDS, SEASON_CODE
    uid = interaction.user.id
    async with SessionLocal() as session:
        if name in ("user", "user_id", "to_discord_id"):
            users = (await session.execute(select(User).order_by(User.username))).scalars().all()
            choices = {u.discord_id: u.username for u in users}
            for member in getattr(interaction.guild, "members", []):
                if not member.bot:
                    choices[member.id] = member.display_name
            if name != "user_id":
                choices.pop(uid, None)
            return [(f"{label} · {did}", did) for did, label in sorted(choices.items(), key=lambda pair: pair[1])]
        if name == "pokemon_id":
            stmt = select(PokemonInstance).join(User, User.id == PokemonInstance.owner_id).where(User.discord_id == uid)
            if action not in ("pokemon_info",):
                stmt = stmt.where(PokemonInstance.locked.is_(False))
            if action in ("market_list", "auction_start"):
                stmt = stmt.where(PokemonInstance.favorite.is_(False),
                                  ~PokemonInstance.id.in_(select(PartySlot.pokemon_id)))
            mons = (await session.execute(stmt.order_by(PokemonInstance.id))).scalars().all()
            return [(f'{m.display_name} · Lv.{m.level} · #{m.id}', m.id) for m in mons]
        if name == "listing_id":
            stmt = select(MarketListing, PokemonInstance).join(PokemonInstance).where(MarketListing.status == "active")
            stmt = stmt.where(MarketListing.seller_discord_id == uid) if action == "market_remove" else stmt.where(MarketListing.seller_discord_id != uid)
            rows = (await session.execute(stmt.order_by(MarketListing.id))).all()
            return [(f'{m.species} · {row.price:,} gold · #{row.id}', row.id) for row, m in rows]
        if name == "auction_id":
            stmt = select(Auction, PokemonInstance).join(PokemonInstance).where(Auction.status == "active")
            if action == "auction_bid":
                stmt = stmt.where(Auction.ends_at > datetime.utcnow(), Auction.seller_discord_id != uid)
            else:
                stmt = stmt.where(Auction.ends_at <= datetime.utcnow())
            rows = (await session.execute(stmt.order_by(Auction.id))).all()
            return [(f'{m.species} · {max(a.starting_bid, a.current_bid + a.bid_increment):,} gold · #{a.id}', a.id) for a, m in rows]
        if action == "auction_bid" and name == "amount":
            auction = await session.get(Auction, values["auction_id"])
            if not auction:
                return []
            minimum = max(auction.starting_bid, auction.current_bid + auction.bid_increment)
            return [(f'{minimum + i * auction.bid_increment:,} gold', minimum + i * auction.bid_increment) for i in (0, 1, 2, 5)]
        if name == "offer_id":
            participant = TradeOffer.to_discord_id if action == "trade_accept" else TradeOffer.from_discord_id
            rows = (await session.execute(select(TradeOffer).where(TradeOffer.status == "open", participant == uid).order_by(TradeOffer.id))).scalars().all()
            return [(f'Trade #{r.id} · {r.offered_json[:35]} → {r.requested_json[:35]}', r.id) for r in rows]
        if name == "request_id":
            rows = (await session.execute(select(Friendship, User).outerjoin(User, User.discord_id == Friendship.requester_discord_id)
                .where(Friendship.status == "pending", Friendship.addressee_discord_id == uid))).all()
            return [(f'{u.username if u else r.requester_discord_id} · Request #{r.id}', r.id) for r, u in rows]
        if name == "battle_id":
            if action == "replay_view":
                rows = (await session.execute(select(BattleReplay).order_by(BattleReplay.battle_id.desc()))).scalars().all()
                return [(f'{r.battle_type.title()} battle #{r.battle_id}', r.battle_id) for r in rows]
            stmt = select(ActiveBattle).order_by(ActiveBattle.id.desc())
            if action == "debug_cleanup_finished_battle":
                stmt = stmt.where(ActiveBattle.finished.is_(True))
            rows = (await session.execute(stmt)).scalars().all()
            return [(f'{r.battle_type.title()} battle #{r.id}', r.id) for r in rows]
        if name == "tier":
            user = (await session.execute(select(User).where(User.discord_id == uid))).scalar_one_or_none()
            if not user:
                return []
            claimed = set((await session.execute(select(SeasonRewardClaim.tier).where(
                SeasonRewardClaim.discord_id == uid, SeasonRewardClaim.season_code == SEASON_CODE))).scalars())
            return [(f'Tier {tier} · {qty} {sku.replace("_", " ")}', tier)
                    for tier, (sku, qty) in REWARDS.items() if tier <= SeasonPassService.tier(user.season_xp) and tier not in claimed]
    return []
