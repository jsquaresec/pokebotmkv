from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter(prefix="/shop", tags=["shop"])

@router.get("/catalog")
async def shop_catalog():
    return json.loads(Path("data/shop_catalog.json").read_text(encoding="utf-8"))
