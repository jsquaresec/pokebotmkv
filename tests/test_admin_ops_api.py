def run():
    from config import settings

    settings.enable_debug_cogs = True
    from api.dashboard import app

    routes = [r.path for r in app.routes]
    assert "/admin/ops/queue/reset" in routes
    assert "/admin/ops/battle/{battle_id}/force-finish" in routes
    print("admin ops api tests passed")


if __name__ == "__main__":
    run()
