import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import PriceCache
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _without_system_proxy():
    """AKShare 走东方财富；Windows 系统代理失效时会导致 ProxyError。"""
    import requests
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        orig = requests.sessions.Session.merge_environment_settings

        def _no_proxy_merge(self, url, proxies, stream, verify, cert):
            return {"verify": verify, "cert": cert, "proxies": {}, "stream": stream}

        requests.sessions.Session.merge_environment_settings = _no_proxy_merge
        try:
            yield
        finally:
            requests.sessions.Session.merge_environment_settings = orig

    return _ctx()


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
    code = stock_code.strip().zfill(6)
    import time

    for attempt in range(3):
        try:
            with _without_system_proxy():
                import akshare as ak

                start = (trade_date - timedelta(days=15)).strftime("%Y%m%d")
                end = trade_date.strftime("%Y%m%d")
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start,
                    end_date=end,
                    adjust="",
                )
            if df is None or df.empty:
                return None
            col_date = "日期" if "日期" in df.columns else df.columns[0]
            col_close = "收盘" if "收盘" in df.columns else df.columns[4]
            df = df.copy()
            df["_d"] = df[col_date].astype(str).str.slice(0, 10)
            target = trade_date.isoformat()
            hit = df[df["_d"] == target]
            if not hit.empty:
                return float(hit.iloc[-1][col_close])
            before = df[df["_d"] <= target]
            if before.empty:
                return None
            return float(before.iloc[-1][col_close])
        except Exception as exc:
            logger.warning("akshare 抓取失败 %s %s (第%s次): %s", code, trade_date, attempt + 1, exc)
            if attempt < 2:
                time.sleep(0.8)
    return None


def lookup_stock_name(stock_code: str) -> str | None:
    code = stock_code.strip().zfill(6)
    try:
        with _without_system_proxy():
            import akshare as ak

            df = ak.stock_info_a_code_name()
        row = df[df["code"] == code]
        if row.empty:
            return None
        return str(row.iloc[0]["name"])
    except Exception as exc:
        logger.warning("akshare 查名称失败 %s: %s", code, exc)
        names = {
            "600519": "贵州茅台",
            "300750": "宁德时代",
            "002594": "比亚迪",
            "601318": "中国平安",
            "300843": "胜蓝股份",
        }
        return names.get(code)


def get_close_on_or_before(
    db: Session, stock_code: str, trade_date: date, max_lookback: int = 10
) -> tuple[float, date] | None:
    """取到期日（或之前最近交易日）的收盘价。"""
    for i in range(max_lookback + 1):
        d = trade_date - timedelta(days=i)
        close = get_close_price(db, stock_code, d)
        if close is not None:
            return close, d
    return None


def add_trading_days(start: date, n: int) -> date:
    """简化：按自然日加；生产可换交易日历表。"""
    return start + timedelta(days=n)
