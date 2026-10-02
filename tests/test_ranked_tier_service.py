from services.ranked_tier_service import RankedTierService

def run():
    svc = RankedTierService()
    assert svc.tier_for_rating(1000) == "Bronze"
    assert svc.tier_for_rating(1250) == "Silver"
    assert svc.tier_for_rating(1450) == "Gold"
    assert svc.tier_for_rating(1700) == "Elite"
    print("ranked tier service tests passed")

if __name__ == "__main__":
    run()
