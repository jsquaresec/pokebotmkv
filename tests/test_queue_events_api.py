def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/queue/events" in routes
    print("queue events api tests passed")

if __name__ == "__main__":
    run()
