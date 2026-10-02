class AdminPlaytestService:
    def __init__(self):
        self.currency_grants = []
        self.resets = []

    def grant_test_currency(self, user_id: int, amount: int) -> dict:
        row = {"user_id": user_id, "amount": amount}
        self.currency_grants.append(row)
        return row

    def reset_user_state(self, user_id: int) -> dict:
        row = {"user_id": user_id, "status": "reset"}
        self.resets.append(row)
        return row
