class MarketService:
    def __init__(self):
        self.listings = []

    def list_item(self, seller_id, item, price):
        listing = {"seller": seller_id, "item": item, "price": price}
        self.listings.append(listing)
        return listing

    def buy_item(self, buyer_id, index):
        if index >= len(self.listings):
            raise ValueError("Invalid listing")
        return self.listings.pop(index)
