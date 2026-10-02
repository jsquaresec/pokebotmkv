from services.market_fee_service import MarketFeeService

def run():
    svc = MarketFeeService()
    assert svc.listing_fee(100) >= 1
    assert svc.sale_fee(100) >= svc.listing_fee(100)
    print("market fee service tests passed")

if __name__ == "__main__":
    run()
