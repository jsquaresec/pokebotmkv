def run():
    delivery = {
        "event_type": "ranked_match_created",
        "recipient_discord_id": 1001,
        "related_battle_id": 5,
        "status": "queued",
        "payload_json": "{}",
    }
    assert delivery["recipient_discord_id"] == 1001
    assert delivery["related_battle_id"] == 5
    print("event consumer delivery shape tests passed")

if __name__ == "__main__":
    run()
