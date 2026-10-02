from datetime import datetime, timedelta
import pytest
from sqlalchemy import select
from models.inventory_item import InventoryItem
from services.daily_mission_service import DailyMissionService, MISSIONS, TIERS
from test_daily_reward_service import db

async def test_board_persists_and_claim_is_once(db):
    svc = DailyMissionService(db)
    now = datetime(2026, 10, 1, 12)
    rows = await svc.board(123, now)
    original = [(r.code, r.reward_sku, r.reward_quantity) for r in rows]
    await db.commit()
    assert len(rows) == 9
    assert all((r.reward_sku, r.reward_quantity) in TIERS[MISSIONS[r.code]['tier']]['rewards'] for r in rows)
    assert original == [(r.code, r.reward_sku, r.reward_quantity) for r in await svc.board(123, now)]
    with pytest.raises(ValueError, match='Complete'):
        await svc.claim(123, 'catch_easy', now.date(), now)
    await svc.record(123, 'catch', now)
    await svc.record(123, 'catch', now)
    reward = await svc.claim(123, 'catch_easy', now.date(), now)
    await db.commit()
    item = await db.scalar(select(InventoryItem).where(InventoryItem.sku == reward.reward_sku))
    assert item.quantity == reward.reward_quantity
    with pytest.raises(ValueError, match='already'):
        await svc.claim(123, 'catch_easy', now.date(), now)

async def test_new_day_and_stale_claim(db):
    svc = DailyMissionService(db)
    now = datetime(2026, 10, 1, 23, 59)
    await svc.record(123, 'shop', now)
    await db.commit()
    tomorrow = now + timedelta(minutes=1)
    rows = await svc.board(123, tomorrow)
    assert all(r.progress == 0 and r.claimed_at is None for r in rows)
    with pytest.raises(ValueError, match='expired'):
        await svc.claim(123, 'shop_easy', now.date(), tomorrow)

async def test_reward_rollback(db):
    svc = DailyMissionService(db)
    now = datetime(2026, 10, 1)
    await svc.record(123, 'battle', now)
    await db.commit()
    await svc.claim(123, 'battle_easy', now.date(), now)
    await db.rollback()
    assert await db.scalar(select(InventoryItem)) is None
    row = next(r for r in await svc.board(123, now) if r.code == 'battle_easy')
    assert row.claimed_at is None

async def test_tier_targets_and_shared_progress(db):
    svc = DailyMissionService(db)
    now = datetime(2026, 10, 1)
    for _ in range(3):
        await svc.record(123, 'catch', now)
    rows = {r.code: r for r in await svc.board(123, now)}
    assert rows['catch_easy'].progress == 1
    assert rows['catch_medium'].progress == 3
    assert rows['catch_hard'].progress == 3
    assert rows['battle_easy'].progress == 0
    await svc.claim(123, 'catch_medium', now.date(), now)
    with pytest.raises(ValueError, match='Complete'):
        await svc.claim(123, 'catch_hard', now.date(), now)
    for _ in range(4):
        await svc.record(123, 'catch', now)
    reward = await svc.claim(123, 'catch_hard', now.date(), now)
    assert (reward.reward_sku, reward.reward_quantity) in TIERS['hard']['rewards']

async def test_shop_purchase_advances_missions(db):
    from services.shop_service import ShopService
    from repositories.inventory import InventoryRepository
    from repositories.users import UserRepository
    user = await UserRepository(db).get_by_discord_id_locked(123)
    await ShopService(InventoryRepository(db)).purchase(user, 'poke_ball', 2)
    rows = await DailyMissionService(db).board(123)
    assert all(r.progress == 1 for r in rows if MISSIONS[r.code]['event'] == 'shop')
    assert all(r.progress == 0 for r in rows if MISSIONS[r.code]['event'] == 'catch')

async def test_gui_tier_buttons(db, monkeypatch):
    from contextlib import asynccontextmanager
    import core.daily_mission_view as gui
    from gui_fakes import interaction
    @asynccontextmanager
    async def session():
        yield db
    monkeypatch.setattr(gui, 'SessionLocal', session)
    click = interaction(user_id=123)
    await gui.show_missions(click, tier='hard')
    from core.private_panels import PANELS
    panel = next(iter(PANELS.values()))
    labels = [button.label for button in panel.view.children]
    assert labels[:4] == ['Home', 'Easy', 'Medium', 'Hard']
    assert len(labels) == 7
    assert all(button.disabled for button in panel.view.children[4:])
