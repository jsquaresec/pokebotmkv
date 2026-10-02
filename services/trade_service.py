import json
from repositories.trade_offers import TradeOfferRepository
from services.transfer_guard import ensure_not_in_party

class TradeService:
    def __init__(self, repo: TradeOfferRepository):
        self.repo = repo

    async def create_offer(self, from_discord_id: int, to_discord_id: int, offered: dict, requested: dict):
        if from_discord_id == to_discord_id:
            raise ValueError("Cannot trade with yourself.")
        for asset in (offered, requested):
            if type(asset.get("quantity", 1)) is not int or asset.get("quantity", 1) <= 0:
                raise ValueError("Quantity must be a positive integer.")
            if not asset.get("sku") and not asset.get("pokemon_id"):
                raise ValueError("An asset is required.")
        return await self.repo.create(
            from_discord_id=from_discord_id,
            to_discord_id=to_discord_id,
            offered_json=json.dumps(offered),
            requested_json=json.dumps(requested),
            status="open",
        )

    async def recent(self, limit: int = 50):
        return await self.repo.latest(limit)

    async def settle(self, offer_id: int, accepting_discord_id: int, session, users, inventory, pokemon):
        offer = await self.repo.get(offer_id, lock=True)
        if not offer or offer.status != "open":
            raise ValueError("Trade offer is not open.")
        if offer.to_discord_id != accepting_discord_id:
            raise ValueError("Only the recipient can accept this offer.")
        source = await users.get_by_discord_id_locked(offer.from_discord_id)
        target = await users.get_by_discord_id_locked(offer.to_discord_id)
        if not source or not target:
            raise ValueError("Both trainers must have profiles.")
        offered = json.loads(offer.offered_json)
        requested = json.loads(offer.requested_json)
        await self._transfer(offered, source, target, inventory, pokemon)
        await self._transfer(requested, target, source, inventory, pokemon)
        offer.status = "accepted"
        await session.flush()
        return offer

    async def _transfer(self, asset, source, target, inventory, pokemon):
        quantity = int(asset.get("quantity", 1))
        if quantity <= 0:
            raise ValueError("Trade quantities must be positive.")
        if "pokemon_id" in asset:
            mon = await pokemon.get_by_id_locked(int(asset["pokemon_id"]))
            if not mon or mon.owner_id != source.id or mon.locked or mon.favorite:
                raise ValueError("Pokémon ownership validation failed.")
            await ensure_not_in_party(pokemon.session, mon.id)
            mon.owner_id = target.id
            return
        if asset.get("sku") == "coins":
            if source.balance < quantity:
                raise ValueError("Insufficient coins.")
            source.balance -= quantity
            target.balance += quantity
            return
        sku = asset.get("sku")
        row = await inventory.get_item_locked(source.discord_id, sku)
        if not row or row.quantity < quantity:
            raise ValueError(f"Insufficient {sku}.")
        row.quantity -= quantity
        await inventory.add_item(target.discord_id, sku, quantity)

    async def cancel(self, offer_id: int, actor_discord_id: int, session):
        offer = await self.repo.get(offer_id, lock=True)
        if not offer or offer.status != "open" or actor_discord_id not in {offer.from_discord_id, offer.to_discord_id}:
            raise ValueError("Open trade offer not found.")
        offer.status = "cancelled"
        await session.flush()
        return offer
