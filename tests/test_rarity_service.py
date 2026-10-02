from services.rarity_service import RarityService

def run():
    svc = RarityService()
    rarity = svc.roll_rarity()
    assert rarity in svc.RARITY_WEIGHTS
    style = svc.style_for("rare")
    assert style["label"] == "RARE"
    assert svc.reward_multiplier("legendary") > svc.reward_multiplier("common")
    print("rarity service tests passed")

if __name__ == "__main__":
    run()
