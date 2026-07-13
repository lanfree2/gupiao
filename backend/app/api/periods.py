from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, DbSession
from app.models import UserPeriod
from app.schemas import PeriodIn, PeriodOut
from app.services.period_calc import due_date_for_period, normalize_period_unit, suggest_label

router = APIRouter(prefix="/periods", tags=["追踪周期"])


def _sort_key(p: PeriodIn) -> tuple:
    _, unit = normalize_period_unit(p.label, p.days, p.unit)
    if unit == "natural_month":
        return (p.days * 30, 0)
    if unit == "natural_week":
        return (p.days * 7, 1)
    return (p.days, 2)


@router.get("", response_model=list[PeriodOut])
def list_periods(user: CurrentUser, db: DbSession):
    from app.services.tracking import ensure_user_periods

    periods = ensure_user_periods(db, user.id)
    return [PeriodOut.model_validate(p) for p in periods]


@router.put("", response_model=list[PeriodOut])
def replace_periods(body: list[PeriodIn], user: CurrentUser, db: DbSession):
    if not body:
        raise HTTPException(status_code=400, detail="至少保留一个周期")
    db.query(UserPeriod).filter(UserPeriod.user_id == user.id).delete()
    for i, p in enumerate(sorted(body, key=_sort_key)):
        days, unit = normalize_period_unit(p.label.strip(), p.days, p.unit)
        label = p.label.strip() or suggest_label(unit, days)
        db.add(
            UserPeriod(
                user_id=user.id,
                label=label,
                days=days,
                unit=unit,
                sort_order=i,
            )
        )
    db.commit()
    periods = db.query(UserPeriod).filter(UserPeriod.user_id == user.id).order_by(UserPeriod.sort_order).all()
    from app.services.tracking import sync_tracking_nodes_for_user

    sync_tracking_nodes_for_user(db, user.id)
    return [PeriodOut.model_validate(p) for p in periods]


@router.post("/preview")
def preview_periods(body: list[PeriodIn], user: CurrentUser, start_date: str | None = None):
    from datetime import date as date_cls

    base = date_cls.fromisoformat(start_date) if start_date else date_cls.today()
    rows = []
    for p in sorted(body, key=_sort_key):
        days, unit = normalize_period_unit(p.label.strip(), p.days, p.unit)
        due = due_date_for_period(base, unit, days)
        rows.append({"label": p.label.strip() or suggest_label(unit, days), "unit": unit, "days": days, "due_date": due.isoformat()})
    return {"start_date": base.isoformat(), "items": rows}
