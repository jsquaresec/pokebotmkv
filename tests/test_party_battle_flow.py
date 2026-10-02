from battle.party_builder import build_team_state

class DummyMon:
    def __init__(self, mon_id, name, hp, attack, defense, speed):
        self.id = mon_id
        self.species = name
        self.current_hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.speed = speed

def run():
    team = [
        DummyMon(1, "Pikachu", 20, 12, 7, 10),
        DummyMon(2, "Eevee", 18, 9, 9, 9),
        DummyMon(3, "Charmander", 19, 11, 8, 11),
    ]
    built = build_team_state(team)
    assert built["active"]["name"] == "Pikachu"
    assert len(built["bench"]) == 2
    assert built["bench"][0]["name"] == "Eevee"
    print("party battle flow tests passed")

if __name__ == "__main__":
    run()
