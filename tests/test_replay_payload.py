import json

def run():
    payload = {
        "battle_id": 5,
        "battle_type": "ranked",
        "winner_discord_id": 123,
        "turn": 4,
        "log": ["A hit B", "B fainted"],
    }
    raw = json.dumps(payload)
    parsed = json.loads(raw)

    assert parsed["battle_id"] == 5
    assert parsed["battle_type"] == "ranked"
    assert parsed["winner_discord_id"] == 123
    assert len(parsed["log"]) == 2
    print("replay payload tests passed")

if __name__ == "__main__":
    run()
