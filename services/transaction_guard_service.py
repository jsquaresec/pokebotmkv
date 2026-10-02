class TransactionGuardService:
    def ensure_positive_quantity(self, quantity: int) -> int:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        return quantity

    def ensure_user_exists(self, user) -> None:
        if user is None:
            raise ValueError("Use `/start` first.")

    def ensure_open_offer(self, offer) -> None:
        if offer is None:
            raise ValueError("Trade offer not found.")
        if getattr(offer, "status", None) != "open":
            raise ValueError("Trade offer is not open.")
