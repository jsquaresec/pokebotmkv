from services.onboarding_guide_service import OnboardingGuideService

def run():
    svc = OnboardingGuideService()
    start = svc.quick_start()
    tips = svc.beginner_tips()
    assert "Catch" in start
    assert len(tips) >= 2
    print("onboarding guide service tests passed")

if __name__ == "__main__":
    run()
