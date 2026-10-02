from datetime import datetime, timedelta
from repositories.auctions import AuctionRepository
from repositories.pokemon import PokemonRepository
from repositories.users import UserRepository
from services.market_fee_service import MarketFeeService
from services.idempotency_service import IdempotencyService
from services.transfer_guard import ensure_not_in_party


class AuctionService:
    def __init__(self, session):
        self.session = session
        self.auctions = AuctionRepository(session)
        self.pokemon = PokemonRepository(session)
        self.users = UserRepository(session)

    async def start(
        self, seller_discord_id: int, pokemon_id: int, duration_hours: int, starting_bid: int, bid_increment: int
    ):
        if not 1 <= duration_hours <= 168:
            raise ValueError("Auction duration must be between 1 hour and 7 days.")
        if starting_bid < 10 or bid_increment < 1 or bid_increment > starting_bid:
            raise ValueError("Invalid starting bid or bid increment.")
        seller = await self.users.get_by_discord_id_locked(seller_discord_id)
        mon = await self.pokemon.get_by_id_locked(pokemon_id)
        if not seller or not mon or mon.owner_id != seller.id or mon.locked or mon.favorite:
            raise ValueError("That Pokémon cannot be auctioned.")
        await ensure_not_in_party(self.session, mon.id)
        mon.locked = True
        return await self.auctions.create(
            pokemon_id=mon.id,
            seller_discord_id=seller_discord_id,
            starting_bid=starting_bid,
            current_bid=starting_bid - bid_increment,
            bid_increment=bid_increment,
            ends_at=datetime.utcnow() + timedelta(hours=duration_hours),
        )

    async def bid(self, bidder_discord_id: int, auction_id: int, amount: int, request_key: str | None = None):
        if request_key:
            await IdempotencyService(self.session).acquire("auction_bid", request_key, bidder_discord_id)
        auction = await self.auctions.get(auction_id, lock=True)
        if not auction or auction.status != "active" or auction.ends_at <= datetime.utcnow():
            raise ValueError("That auction is not active.")
        if auction.seller_discord_id == bidder_discord_id:
            raise ValueError("You cannot bid on your own auction.")
        minimum = max(auction.starting_bid, auction.current_bid + auction.bid_increment)
        if amount < minimum:
            raise ValueError(f"Minimum bid is {minimum:,} coins.")
        bidder = await self.users.get_by_discord_id_locked(bidder_discord_id)
        reserved = auction.current_bid if auction.highest_bidder_discord_id == bidder_discord_id else 0
        if not bidder or bidder.balance + reserved < amount:
            raise ValueError("Not enough available coins.")
        if auction.highest_bidder_discord_id:
            previous = await self.users.get_by_discord_id_locked(auction.highest_bidder_discord_id)
            previous.balance += auction.current_bid
        bidder.balance -= amount
        auction.current_bid = amount
        auction.highest_bidder_discord_id = bidder_discord_id
        if auction.ends_at - datetime.utcnow() <= timedelta(minutes=2):
            auction.ends_at += timedelta(minutes=2)
        await self.auctions.add_bid(auction.id, bidder_discord_id, amount)
        return auction

    async def settle(self, auction_id: int):
        auction = await self.auctions.get(auction_id, lock=True)
        if not auction or auction.status != "active":
            raise ValueError("Auction is not active.")
        if auction.ends_at > datetime.utcnow():
            raise ValueError("Auction has not ended.")
        seller = await self.users.get_by_discord_id_locked(auction.seller_discord_id)
        mon = await self.pokemon.get_by_id_locked(auction.pokemon_id)
        if not seller or not mon or mon.owner_id != seller.id or not mon.locked:
            raise ValueError("Auction ownership validation failed.")
        if auction.highest_bidder_discord_id:
            winner = await self.users.get_by_discord_id_locked(auction.highest_bidder_discord_id)
            if not winner:
                raise ValueError("Auction winner profile is missing; settlement requires review.")
            fee = MarketFeeService().sale_fee(auction.current_bid)
            seller.balance += auction.current_bid - fee
            mon.owner_id = winner.id
            auction.status = "sold"
        else:
            fee = 0
            auction.status = "expired"
        mon.locked = False
        await self.session.flush()
        return auction, mon, fee
