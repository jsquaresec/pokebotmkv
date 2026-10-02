from services.premium_embed_theme_service import PremiumEmbedThemeService

def run():
    svc = PremiumEmbedThemeService()
    assert svc.color_for_rarity("legendary") == "gold"
    assert "Trainer" in svc.title_block("Trainer")
    print("premium embed theme service tests passed")

if __name__ == "__main__":
    run()
