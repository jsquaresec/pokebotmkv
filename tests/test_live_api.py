def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/live/daily/{discord_id}" in routes
    assert "/live/quests/{discord_id}" in routes
    print("live api tests passed")

if __name__ == "__main__":
    run()
