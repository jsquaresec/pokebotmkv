def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/notifications/recent" in routes
    assert "/notifications/stats" in routes
    assert "/notifications/dead-letter" in routes
    print("notifications api tests passed")

if __name__ == "__main__":
    run()
