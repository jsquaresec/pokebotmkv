from services.progression_apply_service import ProgressionApplyService

class DummyMon:
    def __init__(self):
        self.species = "Pikachu"
        self.level = 5
        self.max_hp = 20
        self.current_hp = 15
        self.attack = 10
        self.defense = 10
        self.speed = 10

def run():
    svc = ProgressionApplyService()
    mon = DummyMon()
    result = svc.apply_battle_xp_to_party_member(mon, 200)
    assert result["leveled"] is True
    assert result["new_level"] == 6
    print("progression apply service tests passed")

if __name__ == "__main__":
    run()
