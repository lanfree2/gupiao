"""周期到期日计算：交易日跳过周末；周/月为自然日历。"""

import calendar
from datetime import date, timedelta

from app.models import UserPeriod

UNIT_TRADING_DAY = "trading_day"
UNIT_NATURAL_WEEK = "natural_week"
UNIT_NATURAL_MONTH = "natural_month"

DEFAULT_PERIODS: list[tuple[str, int, str]] = [
    ("1交易日", 1, UNIT_TRADING_DAY),
    ("3交易日", 3, UNIT_TRADING_DAY),
    ("1周", 1, UNIT_NATURAL_WEEK),
    ("2周", 2, UNIT_NATURAL_WEEK),
    ("1月", 1, UNIT_NATURAL_MONTH),
]


def infer_unit_from_label(label: str) -> str:
    if "周" in label:
        return UNIT_NATURAL_WEEK
    if "月" in label:
        return UNIT_NATURAL_MONTH
    return UNIT_TRADING_DAY


def normalize_period_unit(label: str, days: int, unit: str | None = None) -> tuple[int, str]:
    u = unit or infer_unit_from_label(label)
    if u == UNIT_NATURAL_WEEK:
        if days >= 7 and days % 7 == 0:
            return days // 7, u
        return max(1, days), u
    if u == UNIT_NATURAL_MONTH:
        if days >= 28 and days % 30 == 0:
            return max(1, days // 30), u
        if days in (30, 60, 90):
            return {30: 1, 60: 2, 90: 3}[days], u
        return max(1, days), u
    return max(1, days), UNIT_TRADING_DAY


def add_trading_days(start: date, n: int) -> date:
    """从起始日往后数 n 个交易日（跳过周六日）。"""
    if n <= 0:
        return start
    d = start
    counted = 0
    while counted < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            counted += 1
    return d


def add_natural_weeks(start: date, weeks: int) -> date:
    return start + timedelta(days=7 * max(1, weeks))


def add_natural_months(start: date, months: int) -> date:
    months = max(1, months)
    m = start.month - 1 + months
    y = start.year + m // 12
    m = m % 12 + 1
    last_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(start.day, last_day))


def due_date_for_period(start: date, unit: str, value: int) -> date:
    if unit == UNIT_NATURAL_WEEK:
        return add_natural_weeks(start, value)
    if unit == UNIT_NATURAL_MONTH:
        return add_natural_months(start, value)
    return add_trading_days(start, value)


def due_date_for_user_period(start: date, period: UserPeriod) -> date:
    unit = getattr(period, "unit", None) or infer_unit_from_label(period.label)
    return due_date_for_period(start, unit, period.days)


def period_unit_label(unit: str, value: int) -> str:
    if unit == UNIT_NATURAL_WEEK:
        return f"{value}自然周"
    if unit == UNIT_NATURAL_MONTH:
        return f"{value}自然月"
    return f"{value}交易日"


def suggest_label(unit: str, value: int) -> str:
    if unit == UNIT_NATURAL_WEEK:
        return f"{value}周"
    if unit == UNIT_NATURAL_MONTH:
        return f"{value}月"
    return f"{value}交易日"
