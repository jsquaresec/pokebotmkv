def run():
    from api.dashboard import app
    routes = [r.path for r in app.routes]
    assert "/shop/catalog" in routes
    assert "/inventory/recent/{discord_id}" in routes
    print("shop/inventory api tests passed")

if __name__ == "__main__":
    run()
