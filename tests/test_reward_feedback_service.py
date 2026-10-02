from services.reward_feedback_service import RewardFeedbackService

def run():
    svc = RewardFeedbackService()
    rewards = svc.catch_rewards(1.5, 2)
    assert rewards["XP"] > 100
    assert "Coins" in rewards
    print("reward feedback service tests passed")

if __name__ == "__main__":
    run()
