class MarketFeeService:
    def listing_fee(self, price: int) -> int:
        return max(1, int(price * 0.05))

    def sale_fee(self, price: int) -> int:
        return max(1, int(price * 0.08))
