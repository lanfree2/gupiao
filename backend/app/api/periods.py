from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, DbSession
from app.models import UserPeriod
from app.schemas import MessageOut, PeriodIn, PeriodOut

router = APIRouter(prefix="/periods", tags=["追踪周期"])


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
    for i, p in enumerate(sorted(body, key=lambda x: x.days)):
        db.add(UserPeriod(user_id=user.id, label=p.label, days=p.days, sort_order=i))
    db.commit()
    periods = db.query(UserPeriod).filter(UserPeriod.user_id == user.id).order_by(UserPeriod.sort_order).all()
    return [PeriodOut.model_validate(p) for p in periods]
