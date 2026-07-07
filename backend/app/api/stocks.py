from fastapi import APIRouter

from app.services.market_data import lookup_stock_name

router = APIRouter(prefix="/stocks", tags=["股票"])


@router.get("/lookup")
def stock_lookup(code: str):
    name = lookup_stock_name(code)
    return {"code": code, "name": name or "（未识别）"}
