from services.embed_factory import EmbedFactory

def run():
    svc = EmbedFactory()
    msg = svc.spawn_card("Bulbasaur", "RARE", 5)
    assert "Bulbasaur" in msg
    card = svc.catch_card("Pikachu", "rare", 7, {"XP": 100}, ["Try /profile"])
    assert "Rewards" in card
    print("embed factory tests passed")

if __name__ == "__main__":
    run()
