from services.reward_balance_service import RewardBalanceService

def run():
    svc = RewardBalanceService()
    assert svc.adjusted_coins(100, 1.5) == 150
    assert svc.adjusted_xp(100, 2.0) == 200
    print("reward balance service tests passed")

if __name__ == "__main__":
    run()
