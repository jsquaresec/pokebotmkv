from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User, PokemonInstance, InventoryItem, Auction, PartySlot
from repositories.pokedex import PokedexRepository
from repositories.pokemon import PokemonRepository
from repositories.inventory import InventoryRepository
from services.market_v70_service import MarketV70Service
from services.auction_service import AuctionService
from services.item_action_service import ItemActionService
from services.trainer_progression_service import TrainerProgressionService


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add_all([User(id=1, discord_id=100, username="seller", balance=10000),
                         User(id=2, discord_id=200, username="buyer", balance=1000)])
        session.add(PokemonInstance(id=1, owner_id=1, species="Pikachu"))
        await session.commit()
        yield session
    await engine.dispose()


async def test_first_catch_and_repeat_are_persisted(session):
    repo = PokedexRepository(session)
    await repo.record(100, "Pikachu", True)
    await session.commit()
    await repo.record(100, "Pikachu", True)
    await session.commit()
    assert await repo.summary(100) == {"species_seen": 1, "total_catches": 2}


async def test_self_raise_uses_reserved_balance(session):
    auction = Auction(pokemon_id=1, seller_discord_id=100, highest_bidder_discord_id=200,
                      starting_bid=100, current_bid=900, bid_increment=10,
                      ends_at=datetime.utcnow()+timedelta(hours=1))
    session.add(auction)
    buyer = await session.get(User, 2)
    buyer.balance = 100
    await session.commit()
    await AuctionService(session).bid(200, auction.id, 950)
    await session.commit()
    assert buyer.balance == 50
    assert auction.current_bid == 950


async def test_market_cancel_relist_purchase(session):
    svc = MarketV70Service(session)
    listing, _ = await svc.list_pokemon(100, 1, 100)
    await session.commit()
    await svc.cancel(100, listing.id)
    await session.commit()
    second, _ = await svc.list_pokemon(100, 1, 100)
    await session.commit()
    mon, fee = await svc.buy(200, second.id)
    await session.commit()
    assert second.id != listing.id
    assert mon.owner_id == 2
    assert fee == 8
    assert (await session.get(User, 2)).balance == 900
    with pytest.raises(ValueError):
        await svc.buy(200, second.id)


async def test_party_member_cannot_be_listed(session):
    session.add(PartySlot(owner_id=1, pokemon_id=1, slot_index=1))
    await session.commit()
    with pytest.raises(ValueError, match="party"):
        await MarketV70Service(session).list_pokemon(100, 1, 100)
    assert not (await session.get(PokemonInstance, 1)).locked


async def test_candy_cap_preserves_inventory(session):
    mon = await session.get(PokemonInstance, 1)
    mon.level = 100
    item = InventoryItem(owner_discord_id=100, sku="rare_candy", quantity=1)
    session.add(item)
    await session.commit()
    svc = ItemActionService(session, InventoryRepository(session), PokemonRepository(session))
    with pytest.raises(ValueError, match="cap"):
        await svc.use(100, 1, 1, "rare_candy")
    assert item.quantity == 1


async def test_collection_pagination(session):
    session.add_all([PokemonInstance(owner_id=1, species="Pikachu") for _ in range(205)])
    await session.commit()
    rows = await PokemonRepository(session).search(1, limit=20, page=11)
    assert len(rows) == 6


def test_trainer_xp_persisted_defaults():
    user = SimpleNamespace(trainer_level=1, trainer_xp=0, season_xp=0)
    TrainerProgressionService().grant(user, 150)
    assert (user.trainer_level, user.trainer_xp, user.season_xp) == (2, 50, 150)


async def test_full_catch_transaction(session):
    from models.wild_encounter import WildEncounter
    from repositories.users import UserRepository
    from services.encounter_v70_service import EncounterV70Service
    session.add(InventoryItem(owner_discord_id=100, sku="master_ball", quantity=1))
    session.add(WildEncounter(guild_id=1, channel_id=2, species="Pikachu", level=5,
                             current_hp=20, max_hp=20, expires_at=datetime.utcnow()+timedelta(minutes=1)))
    await session.commit()
    mon = await EncounterV70Service(session).attempt_catch(2, 100, "master_ball", UserRepository(session), InventoryRepository(session))
    await session.commit()
    assert mon.owner_id == 1
    await session.refresh(await session.get(User, 1))
    assert (await session.get(User, 1)).balance == 10500
    assert (await PokedexRepository(session).summary(100))["total_catches"] == 1
    assert (await InventoryRepository(session).get_item(100, "master_ball")).quantity == 0
    with pytest.raises(ValueError):
        await EncounterV70Service(session).attempt_catch(2, 100, "master_ball", UserRepository(session), InventoryRepository(session))
    assert (await session.get(User, 1)).balance == 10500


async def test_failed_catch_does_not_award_gold(session):
    from models.wild_encounter import WildEncounter
    from repositories.users import UserRepository
    from services.encounter_v70_service import EncounterV70Service
    session.add(InventoryItem(owner_discord_id=100, sku="poke_ball", quantity=1))
    session.add(WildEncounter(guild_id=1, channel_id=2, species="Pikachu", level=5,
                             current_hp=20, max_hp=20, expires_at=datetime.utcnow()+timedelta(minutes=1)))
    await session.commit()
    service = EncounterV70Service(session, rng=SimpleNamespace(random=lambda: 1.0))
    mon = await service.attempt_catch(2, 100, "poke_ball", UserRepository(session), InventoryRepository(session))
    await session.commit()
    assert mon is None
    assert (await session.get(User, 1)).balance == 10000
    assert (await InventoryRepository(session).get_item(100, "poke_ball")).quantity == 0
