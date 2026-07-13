from datetime import date

from fastapi import APIRouter, HTTPException

from app.deps import DbSession
from app.services.market_data import get_close_on_or_before, lookup_stock_name

router = APIRouter(prefix="/stocks", tags=["股票"])


@router.get("/lookup")
def stock_lookup(code: str):
    norm = code.strip()
    if len("".join(ch for ch in norm if ch.isdigit())) < 6:
        raise HTTPException(status_code=400, detail="请输入 6 位股票代码")
    name = lookup_stock_name(norm)
    return {"code": norm.zfill(6)[-6:], "name": name or "（未识别）"}


@router.get("/close")
def stock_close(code: str, trade_date: str, db: DbSession):
    """查询指定日期（或之前最近交易日）的收盘价，用于录入时自动填价。"""
    try:
        d = date.fromisoformat(trade_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日期格式无效") from exc
    result = get_close_on_or_before(db, code.strip().zfill(6), d)
    if not result:
        raise HTTPException(
            status_code=503,
            detail="无法连接行情源（请检查服务器外网或代理设置），可手动填写价格",
        )
    close, actual_date = result
    return {"code": code, "trade_date": str(actual_date), "close": close}
