def run():
    from config import settings

    settings.enable_debug_cogs = True
    from api.dashboard import app

    routes = [r.path for r in app.routes]

    assert "/audit/logs" in routes
    assert any("/debug/battle" in r for r in routes)

    print("api debug tests passed")


if __name__ == "__main__":
    run()
