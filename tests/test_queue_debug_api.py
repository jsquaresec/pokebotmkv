def run():
    from config import settings

    settings.enable_debug_cogs = True
    from api.dashboard import app

    routes = [r.path for r in app.routes]
    assert "/queue/status" in routes
    print("queue debug api tests passed")


if __name__ == "__main__":
    run()
