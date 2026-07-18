"""用户维度总览统计，用户端与管理后台复用。"""
from sqlalchemy.orm import Session, joinedload

from app.models import Channel, Recommendation
from app.schemas import RecommendationOut
from app.services.stats import (
    all_node_values,
    collect_node_values,
    count_due_pending_nodes,
    rec_to_out,
    stats_from_values,
)
from app.services.tracking import ensure_user_periods


def build_user_dashboard(db: Session, user_id: int) -> dict:
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == user_id)
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    all_vals = all_node_values(recs)
    win_rate, avg_return = stats_from_values(all_vals)
    pending = count_due_pending_nodes(recs)
    periods = ensure_user_periods(db, user_id)
    period_stats = []
    for p in periods:
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
    channels = db.query(Channel).filter(Channel.user_id == user_id, Channel.is_active.is_(True)).all()
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
        for p in periods:
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
                "id": ch.id,
                "name": ch.name,
                "color": ch.color,
                "record_count": len(ch_recs),
                "win_rate": wr,
                "avg_return": ar,
                "periods": ch_periods,
            }
        )
    recent = [RecommendationOut(**rec_to_out(r)) for r in recs[:8]]
    return {
        "tracking_count": len(recs),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "pending_nodes": pending,
        "channel_win_rates": channel_win_rates,
        "channel_avg_returns": channel_avg_returns,
        "period_stats": period_stats,
        "channel_period_stats": channel_period_stats,
        "recent": recent,
        "periods": [
            {
                "id": p.id,
                "label": p.label,
                "days": p.days,
                "unit": getattr(p, "unit", "trading_day") or "trading_day",
                "sort_order": p.sort_order,
            }
            for p in periods
        ],
    }


def summarize_user_recs(recs: list[Recommendation]) -> dict:
    vals = all_node_values(recs)
    win_rate, avg_return = stats_from_values(vals)
    return {
        "record_count": len(recs),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "pending_nodes": count_due_pending_nodes(recs),
        "stock_count": len({r.stock_code for r in recs}),
        "channel_count": len({r.channel_id for r in recs}),
    }
