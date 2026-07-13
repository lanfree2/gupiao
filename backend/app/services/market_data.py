import logging
import os
from contextlib import contextmanager
from datetime import date, timedelta
from functools import lru_cache

from sqlalchemy.orm import Session

from app.models import PriceCache
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
    "NO_PROXY",
    "no_proxy",
)


@contextmanager
def _without_system_proxy():
    """AKShare 部分源走国内直连；Windows 系统代理常导致连接被远端断开。"""
    import requests

    saved = {k: os.environ.pop(k) for k in _PROXY_KEYS if k in os.environ}
    orig_merge = requests.sessions.Session.merge_environment_settings

    def _no_proxy_merge(self, url, proxies, stream, verify, cert):
        return {"verify": verify, "cert": cert, "proxies": {}, "stream": stream}

    requests.sessions.Session.merge_environment_settings = _no_proxy_merge
    try:
        yield
    finally:
        requests.sessions.Session.merge_environment_settings = orig_merge
        os.environ.update(saved)


def _to_tx_symbol(stock_code: str) -> str:
    code = stock_code.strip().zfill(6)
    if code.startswith(("5", "6", "9")):
        return f"sh{code}"
    return f"sz{code}"


def _cache_get(db: Session, stock_code: str, trade_date: date) -> float | None:
    cached = (
        db.query(PriceCache)
        .filter(PriceCache.stock_code == stock_code, PriceCache.trade_date == trade_date)
        .first()
    )
    return cached.close_price if cached else None


def get_close_price(db: Session, stock_code: str, trade_date: date) -> float | None:
    code = stock_code.strip().zfill(6)
    hit = _cache_get(db, code, trade_date)
    if hit is not None:
        return hit

    price = _fetch_from_provider(code, trade_date)
    if price is not None:
        db.add(
            PriceCache(
                stock_code=code,
                trade_date=trade_date,
                close_price=price,
                source=settings.market_data_provider,
            )
        )
        db.commit()
    return price


def _fetch_from_provider(stock_code: str, trade_date: date) -> float | None:
    if settings.market_data_provider != "akshare":
        return None
    start = trade_date - timedelta(days=15)
    df = _akshare_hist_df(stock_code, start, trade_date)
    return _close_from_hist_df(df, trade_date)


def _akshare_hist_df(stock_code: str, start: date, end: date):
    code = stock_code.strip().zfill(6)
    import time

    fetchers = (
        ("tx", _fetch_hist_tx),
        ("em", _fetch_hist_em),
        ("sina", _fetch_hist_sina),
    )
    for name, fetcher in fetchers:
        for attempt in range(2):
            try:
                df = fetcher(code, start, end)
                if df is not None and not df.empty:
                    return df
            except Exception as exc:
                logger.warning(
                    "akshare %s 抓取失败 %s %s~%s (第%s次): %s",
                    name,
                    code,
                    start,
                    end,
                    attempt + 1,
                    exc,
                )
                if attempt < 1:
                    time.sleep(0.25)
    return None


def _fetch_hist_tx(code: str, start: date, end: date):
    with _without_system_proxy():
        import akshare as ak

        return ak.stock_zh_a_hist_tx(
            symbol=_to_tx_symbol(code),
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )


def _fetch_hist_em(code: str, start: date, end: date):
    with _without_system_proxy():
        import akshare as ak

        return ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )


def _fetch_hist_sina(code: str, start: date, end: date):
    with _without_system_proxy():
        import akshare as ak

        return ak.stock_zh_a_daily(
            symbol=_to_tx_symbol(code),
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="qfq",
        )


def _normalize_hist_df(df):
    if df is None or df.empty:
        return None
    col_date = next((c for c in ("date", "日期", "Date") if c in df.columns), df.columns[0])
    col_close = next((c for c in ("close", "收盘", "Close") if c in df.columns), df.columns[2])
    out = df.copy()
    out["_d"] = out[col_date].astype(str).str.slice(0, 10)
    out["_c"] = out[col_close].astype(float)
    return out


def _close_from_hist_df(df, trade_date: date) -> float | None:
    norm = _normalize_hist_df(df)
    if norm is None:
        return None
    target = trade_date.isoformat()
    hit = norm[norm["_d"] == target]
    if not hit.empty:
        return float(hit.iloc[-1]["_c"])
    before = norm[norm["_d"] <= target]
    if before.empty:
        return None
    return float(before.iloc[-1]["_c"])


def _store_hist_df_to_cache(db: Session, stock_code: str, df) -> int:
    norm = _normalize_hist_df(df)
    if norm is None:
        return 0
    code = stock_code.strip().zfill(6)
    added = 0
    for _, row in norm.iterrows():
        try:
            trade_date = date.fromisoformat(str(row["_d"])[:10])
        except ValueError:
            continue
        if _cache_get(db, code, trade_date) is not None:
            continue
        db.add(
            PriceCache(
                stock_code=code,
                trade_date=trade_date,
                close_price=float(row["_c"]),
                source=settings.market_data_provider,
            )
        )
        added += 1
    if added:
        db.commit()
    return added


def _can_resolve_from_cache(
    db: Session, stock_code: str, trade_date: date, lookback_days: int = 10
) -> bool:
    code = stock_code.strip().zfill(6)
    for i in range(lookback_days + 1):
        if _cache_get(db, code, trade_date - timedelta(days=i)) is not None:
            return True
    return False


def prefetch_close_prices(
    db: Session, stock_code: str, target_dates: list[date], lookback_days: int = 10
) -> None:
    """一次拉取日期区间内的行情并写入缓存，避免每个节点单独请求 AKShare。"""
    if not target_dates:
        return
    code = stock_code.strip().zfill(6)
    if all(_can_resolve_from_cache(db, code, td, lookback_days) for td in target_dates):
        return
    start = min(target_dates) - timedelta(days=lookback_days)
    end = max(target_dates)
    df = _akshare_hist_df(code, start, end)
    _store_hist_df_to_cache(db, code, df)


@lru_cache(maxsize=1)
def _sh_code_name_map() -> dict[str, str]:
    with _without_system_proxy():
        import akshare as ak

        df = ak.stock_info_sh_name_code()
    return _parse_code_name_df(df)


@lru_cache(maxsize=1)
def _sz_code_name_map() -> dict[str, str]:
    with _without_system_proxy():
        import akshare as ak

        df = ak.stock_info_sz_name_code()
    return _parse_code_name_df(df)


@lru_cache(maxsize=1)
def _all_a_code_name_map() -> dict[str, str]:
    with _without_system_proxy():
        import akshare as ak

        df = ak.stock_info_a_code_name()
    return _parse_code_name_df(df)


def _norm_stock_code(value) -> str:
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if "." in s:
        s = s.split(".")[0]
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits.zfill(6)[-6:] if digits else s.zfill(6)


def _parse_code_name_df(df) -> dict[str, str]:
    if df is None or df.empty:
        return {}
    cols = list(df.columns)
    code_col = next(
        (c for c in cols if any(k in str(c) for k in ("代码", "code", "CODE"))),
        cols[0],
    )
    name_col = next(
        (c for c in cols if c != code_col and any(k in str(c) for k in ("简称", "名称", "name", "NAME"))),
        cols[1] if len(cols) > 1 else cols[0],
    )
    out: dict[str, str] = {}
    for _, row in df.iterrows():
        code = _norm_stock_code(row[code_col])
        name = str(row[name_col]).strip()
        if len(code) == 6 and name and name != "nan":
            out[code] = name
    return out


def _to_em_symbol(code: str) -> str:
    if code.startswith(("8", "4")):
        return f"bj{code}"
    if code.startswith(("5", "6", "9")):
        return f"sh{code}"
    return f"sz{code}"


@lru_cache(maxsize=1)
def _bj_code_name_map() -> dict[str, str]:
    with _without_system_proxy():
        import akshare as ak

        try:
            df = ak.stock_info_bj_name_code()
            return _parse_code_name_df(df)
        except Exception:
            return {}


def _lookup_name_spot_em(code: str) -> str | None:
    with _without_system_proxy():
        import akshare as ak

        try:
            df = ak.stock_zh_a_spot_em()
            if df is None or df.empty:
                return None
            code_col = next((c for c in df.columns if "代码" in str(c) or str(c).lower() == "code"), df.columns[0])
            name_col = next((c for c in df.columns if "名称" in str(c) or "简称" in str(c)), df.columns[1])
            for _, row in df.iterrows():
                if _norm_stock_code(row[code_col]) == code:
                    name = str(row[name_col]).strip()
                    if name and name != "nan":
                        return name
        except Exception as exc:
            logger.warning("spot_em 查名称失败 %s: %s", code, exc)
    return None


def _lookup_name_individual_em(code: str) -> str | None:
    with _without_system_proxy():
        import akshare as ak

        try:
            symbol = _to_em_symbol(code)
            df = ak.stock_individual_info_em(symbol=symbol)
            if df is None or df.empty:
                return None
            item_col = df.columns[0]
            val_col = df.columns[1]
            for _, row in df.iterrows():
                if "股票简称" in str(row[item_col]) or "证券简称" in str(row[item_col]):
                    name = str(row[val_col]).strip()
                    if name and name != "nan":
                        return name
        except Exception as exc:
            logger.warning("individual_em 查名称失败 %s: %s", code, exc)
    return None


def lookup_stock_name(stock_code: str) -> str | None:
    code = _norm_stock_code(stock_code)
    if len(code) != 6 or not code.isdigit():
        return None
    try:
        # 单股接口最准确，优先于批量列表（避免错配、创业板等漏查）
        name = _lookup_name_individual_em(code)
        if name:
            return name
        maps: list[dict[str, str]] = []
        if code.startswith(("8", "4")):
            maps.append(_bj_code_name_map())
        elif code.startswith(("5", "6", "9")):
            maps.append(_sh_code_name_map())
        else:
            maps.append(_sz_code_name_map())
        maps.append(_all_a_code_name_map())
        for m in maps:
            hit = m.get(code)
            if hit:
                return hit
        name = _lookup_name_spot_em(code)
        if name:
            return name
    except Exception as exc:
        logger.warning("akshare 查名称失败 %s: %s", code, exc)
    fallback = {
        "600519": "贵州茅台",
        "300750": "宁德时代",
        "002594": "比亚迪",
        "601318": "中国平安",
        "300843": "胜蓝股份",
        "601138": "工业富联",
        "600159": "大龙地产",
        "300059": "东方财富",
        "688981": "中芯国际",
    }
    return fallback.get(code)


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
    from app.services.period_calc import add_trading_days as _add_trading_days

    return _add_trading_days(start, n)
