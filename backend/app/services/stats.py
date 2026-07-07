from sqlalchemy.orm import Session, joinedload

from app.models import Channel, NodeStatus, Recommendation, TrackingNode, User


def pct_display(v: float | None) -> str:
    if v is None:
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


def collect_node_values(recs: list[Recommendation], period_index: int) -> list[float]:
    vals = []
    for r in recs:
        if period_index < len(r.nodes):
            n = r.nodes[period_index]
            if n.status == NodeStatus.done and n.pct_change is not None:
                vals.append(n.pct_change)
    return vals


def stats_from_values(vals: list[float]) -> tuple[float | None, float | None]:
    if not vals:
        return None, None
    wins = sum(1 for v in vals if v > 0)
    win_rate = round(wins / len(vals) * 100, 1)
    avg = round(sum(vals) / len(vals), 2)
    return win_rate, avg


def load_recommendation(db: Session, rec_id: int, user_id: int | None = None) -> Recommendation | None:
    q = db.query(Recommendation).options(
        joinedload(Recommendation.nodes),
        joinedload(Recommendation.channel),
    ).filter(Recommendation.id == rec_id)
    if user_id is not None:
        q = q.filter(Recommendation.user_id == user_id)
    return q.first()


def rec_to_out(rec: Recommendation) -> dict:
    nodes = sorted(rec.nodes, key=lambda n: n.days)
    return {
        "id": rec.id,
        "stock_code": rec.stock_code,
        "stock_name": rec.stock_name,
        "channel_id": rec.channel_id,
        "channel_name": rec.channel.name,
        "channel_color": rec.channel.color,
        "recommend_date": rec.recommend_date,
        "recommend_price": rec.recommend_price,
        "reason": rec.reason,
        "created_at": rec.created_at,
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "days": n.days,
                "due_date": n.due_date,
                "status": n.status.value,
                "close_price": n.close_price,
                "pct_change": n.pct_change,
            }
            for n in nodes
        ],
    }


def all_node_values(recs: list[Recommendation]) -> list[float]:
    vals = []
    for r in recs:
        for n in r.nodes:
            if n.status == NodeStatus.done and n.pct_change is not None:
                vals.append(n.pct_change)
    return vals
