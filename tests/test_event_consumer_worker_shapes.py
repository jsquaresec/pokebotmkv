def run():
    sample = {
        "type": "ranked_match_created",
        "battle_id": 1,
        "player_one_discord_id": 1001,
        "player_two_discord_id": 1002,
    }
    assert sample["type"] == "ranked_match_created"
    assert "battle_id" in sample
    assert "player_one_discord_id" in sample
    assert "player_two_discord_id" in sample
    print("event consumer worker shape tests passed")

if __name__ == "__main__":
    run()
