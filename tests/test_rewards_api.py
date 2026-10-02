def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/rewards/recent" in routes
    print("rewards api tests passed")

if __name__ == "__main__":
    run()
