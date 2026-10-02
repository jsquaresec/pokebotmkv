def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/leaderboard/season" in routes
    print("leaderboard season api tests passed")

if __name__ == "__main__":
    run()
