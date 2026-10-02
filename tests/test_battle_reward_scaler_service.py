from services.battle_reward_scaler_service import BattleRewardScalerService

def run():
    svc = BattleRewardScalerService()
    bronze = svc.scale(100, 200, "Bronze")
    elite = svc.scale(100, 200, "Elite")
    assert elite["coins"] > bronze["coins"]
    assert elite["xp"] > bronze["xp"]
    print("battle reward scaler service tests passed")

if __name__ == "__main__":
    run()
