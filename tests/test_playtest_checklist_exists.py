from pathlib import Path

def run():
    assert Path("PLAYTEST_CHECKLIST.md").exists()
    print("playtest checklist exists test passed")

if __name__ == "__main__":
    run()
