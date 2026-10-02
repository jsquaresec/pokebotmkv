from services.progression_service import ProgressionService

class DummyMon:
    def __init__(self):
        self.level = 5
        self.max_hp = 20
        self.current_hp = 15
        self.attack = 10
        self.defense = 10
        self.speed = 10

def run():
    svc = ProgressionService()
    mon = DummyMon()
    lvl, leveled = svc.apply_xp(mon, 200)
    assert leveled is True
    assert lvl == 6
    assert mon.max_hp == 22
    print("progression service tests passed")

if __name__ == "__main__":
    run()
