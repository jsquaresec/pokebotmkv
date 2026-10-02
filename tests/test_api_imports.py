def run():
    from api.dashboard import app
    routes = [getattr(route, "path", "") for route in app.routes]
    assert "/health" in routes
    assert any(path.startswith("/replays") for path in routes)
    assert any(path.startswith("/rulesets") for path in routes)
    assert any(path.startswith("/live-events") for path in routes)
    assert any(path.startswith("/cosmetics") for path in routes)
    print("api import tests passed")

if __name__ == "__main__":
    run()
