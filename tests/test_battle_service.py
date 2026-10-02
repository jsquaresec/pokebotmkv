from services.battle_service import BattleService

class DummyRepo:
    pass

class DummyMon:
    def __init__(self, mon_id, species, hp, attack, defense, speed):
        self.id = mon_id
        self.species = species
        self.current_hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed

def run():
    service = BattleService(DummyRepo())
    mon1 = DummyMon(1, "Pikachu", 20, 12, 7, 14)
    mon2 = DummyMon(2, "Bulbasaur", 22, 9, 9, 8)

    state = service._build_state(111, 222, mon1, mon2)
    assert state["player_one"]["active"]["name"] == "Pikachu"
    assert state["player_two"]["active"]["name"] == "Bulbasaur"
    assert state["finished"] is False

    state = service.apply_move(state, 111)
    assert len(state["log"]) >= 1
    assert state["player_two"]["active"]["hp"] < state["player_two"]["active"]["max_hp"]

    while not state["finished"]:
        state = service.apply_move(state, 111)

    assert state["winner_discord_id"] in {111, 222}
    print("battle service tests passed")

if __name__ == "__main__":
    run()
