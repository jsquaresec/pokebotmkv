def run():
    demo_users = [
        {"discord_id": 900001, "username": "DemoRed"},
        {"discord_id": 900002, "username": "DemoBlue"},
    ]
    demo_pokemon = [
        {"owner_discord_id": 900001, "species": "Pikachu"},
        {"owner_discord_id": 900002, "species": "Bulbasaur"},
    ]

    assert len(demo_users) == 2
    assert all("discord_id" in x and "username" in x for x in demo_users)
    assert all("owner_discord_id" in x and "species" in x for x in demo_pokemon)
    print("demo seed shape tests passed")

if __name__ == "__main__":
    run()
