from datetime import date

from fastapi import APIRouter, HTTPException

from app.deps import DbSession
from app.services.market_data import get_close_on_or_before, lookup_stock_name

router = APIRouter(prefix="/stocks", tags=["股票"])


@router.get("/lookup")
def stock_lookup(code: str):
    name = lookup_stock_name(code)
    return {"code": code, "name": name or "（未识别）"}


@router.get("/close")
def stock_close(code: str, trade_date: str, db: DbSession):
    """查询指定日期（或之前最近交易日）的收盘价，用于录入时自动填价。"""
    try:
        d = date.fromisoformat(trade_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日期格式无效") from exc
    result = get_close_on_or_before(db, code.strip(), d)
    if not result:
        raise HTTPException(status_code=404, detail="无法获取该日收盘价")
    close, actual_date = result
    return {"code": code, "trade_date": str(actual_date), "close": close}
