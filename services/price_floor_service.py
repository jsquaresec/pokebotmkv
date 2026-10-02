class PriceFloorService:
    FLOORS = {
        "poke_ball": 50,
        "great_ball": 125,
        "ultra_ball": 250,
        "potion": 75,
        "super_potion": 150,
    }

    def floor_for(self, item_code: str) -> int:
        return self.FLOORS.get(item_code, 10)

    def validate_price(self, item_code: str, price: int) -> bool:
        return price >= self.floor_for(item_code)
