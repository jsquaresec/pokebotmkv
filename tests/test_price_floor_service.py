from services.price_floor_service import PriceFloorService

def run():
    svc = PriceFloorService()
    assert svc.validate_price("poke_ball", 50) is True
    assert svc.validate_price("poke_ball", 10) is False
    print("price floor service tests passed")

if __name__ == "__main__":
    run()
