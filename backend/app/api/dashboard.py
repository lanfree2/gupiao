from fastapi import APIRouter
from sqlalchemy.orm import joinedload

from app.deps import CurrentUser, DbSession
from app.models import Channel, Recommendation
from app.schemas import DashboardOut, RecommendationOut
from app.services.stats import all_node_values, collect_node_values, count_due_pending_nodes, rec_to_out, stats_from_values
from app.services.tracking import ensure_user_periods

router = APIRouter(prefix="/dashboard", tags=["总览"])


@router.get("", response_model=DashboardOut)
def dashboard(user: CurrentUser, db: DbSession):
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    all_vals = all_node_values(recs)
    win_rate, avg_return = stats_from_values(all_vals)
    pending = count_due_pending_nodes(recs)
    periods = ensure_user_periods(db, user.id)
    period_stats = []
    for i, p in enumerate(periods):
        vals = collect_node_values(recs, p.label)
        wr, ar = stats_from_values(vals)
        period_stats.append(
            {
                "label": p.label,
                "days": p.days,
                "sample": len(vals),
                "win_rate": wr,
                "avg_return": ar,
            }
        )
    channels = db.query(Channel).filter(Channel.user_id == user.id, Channel.is_active.is_(True)).all()
    channel_win_rates = []
    channel_avg_returns = []
    channel_period_stats = []
    for ch in channels:
        ch_recs = [r for r in recs if r.channel_id == ch.id]
        vals = all_node_values(ch_recs)
        wr, ar = stats_from_values(vals)
        channel_win_rates.append({"name": ch.name, "color": ch.color, "win_rate": wr})
        channel_avg_returns.append({"name": ch.name, "color": ch.color, "avg_return": ar})
        ch_periods = []
        for i, p in enumerate(periods):
            pvals = collect_node_values(ch_recs, p.label)
            pwr, par = stats_from_values(pvals)
            ch_periods.append(
                {
                    "label": p.label,
                    "days": p.days,
                    "sample": len(pvals),
                    "win_rate": pwr,
                    "avg_return": par,
                }
            )
        channel_period_stats.append(
            {
                "name": ch.name,
                "color": ch.color,
                "record_count": len(ch_recs),
                "win_rate": wr,
                "avg_return": ar,
                "periods": ch_periods,
            }
        )
    recent = [RecommendationOut(**rec_to_out(r)) for r in recs[:4]]
    return DashboardOut(
        tracking_count=len(recs),
        win_rate=win_rate,
        avg_return=avg_return,
        pending_nodes=pending,
        channel_win_rates=channel_win_rates,
        channel_avg_returns=channel_avg_returns,
        period_stats=period_stats,
        channel_period_stats=channel_period_stats,
        recent=recent,
    )
