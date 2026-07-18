from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas import DashboardOut
from app.services.dashboard_stats import build_user_dashboard

router = APIRouter(prefix="/dashboard", tags=["总览"])


@router.get("", response_model=DashboardOut)
def dashboard(user: CurrentUser, db: DbSession):
    data = build_user_dashboard(db, user.id)
    return DashboardOut(**{k: v for k, v in data.items() if k != "periods"})
