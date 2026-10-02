def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/leaderboard/global" in routes
    print("leaderboard api tests passed")

if __name__ == "__main__":
    run()
