from fastapi import FastAPI
from fastapi.responses import JSONResponse
import secrets
from api.cosmetics import router as cosmetics_router
from api.inventory import router as inventory_router
from api.leaderboard import router as leaderboard_router
from api.leaderboard_season import router as leaderboard_season_router
from api.live import router as live_router
from api.live_events import router as live_events_router
from api.notifications import router as notifications_router
from api.queue_events import router as queue_events_router
from api.replays import router as replay_router
from api.rewards import router as rewards_router
from api.rulesets import router as ruleset_router
from api.shop import router as shop_router
from config import settings


app = FastAPI(title="PokeBot v90 API", version="90.0.0")


@app.middleware("http")
async def require_api_token(request, call_next):
    if request.url.path != "/health":
        supplied = request.headers.get("Authorization", "")
        if not settings.api_token or not secrets.compare_digest(supplied, "Bearer " + settings.api_token):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
    return await call_next(request)
for router in (
    replay_router, ruleset_router, live_events_router, cosmetics_router,
    queue_events_router, notifications_router, rewards_router, shop_router,
    inventory_router, live_router, leaderboard_router, leaderboard_season_router,
):
    app.include_router(router)

if settings.enable_debug_cogs:
    from api.admin_ops import router as admin_ops_router
    from api.debug import router as debug_router
    from api.queue_debug import router as queue_debug_router

    app.include_router(admin_ops_router)
    app.include_router(debug_router)
    app.include_router(queue_debug_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "90.0.0", "check": "process-only"}
