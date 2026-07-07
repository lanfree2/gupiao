from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import PriceCache
from app.config import get_settings

settings = get_settings()


def get_close_price(db: Session, stock_code: str, trade_date: date) -> float | None:
    cached = (
        db.query(PriceCache)
        .filter(PriceCache.stock_code == stock_code, PriceCache.trade_date == trade_date)
        .first()
    )
    if cached:
        return cached.close_price

    price = _fetch_from_provider(stock_code, trade_date)
    if price is not None:
        db.add(
            PriceCache(
                stock_code=stock_code,
                trade_date=trade_date,
                close_price=price,
                source=settings.market_data_provider,
            )
        )
        db.commit()
    return price


def _fetch_from_provider(stock_code: str, trade_date: date) -> float | None:
    if settings.market_data_provider == "akshare":
        return _akshare_close(stock_code, trade_date)
    return None


def _akshare_close(stock_code: str, trade_date: date) -> float | None:
    try:
        import akshare as ak

        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=trade_date.strftime("%Y%m%d"),
            end_date=trade_date.strftime("%Y%m%d"),
            adjust="",
        )
        if df is None or df.empty:
            return None
        return float(df.iloc[0]["收盘"])
    except Exception:
        return None


def lookup_stock_name(stock_code: str) -> str | None:
    try:
        import akshare as ak

        df = ak.stock_info_a_code_name()
        row = df[df["code"] == stock_code]
        if row.empty:
            return None
        return str(row.iloc[0]["name"])
    except Exception:
        names = {
            "600519": "贵州茅台",
            "300750": "宁德时代",
            "002594": "比亚迪",
            "601318": "中国平安",
        }
        return names.get(stock_code)


def add_trading_days(start: date, n: int) -> date:
    """简化：按自然日加；生产可换交易日历表。"""
    return start + timedelta(days=n)
