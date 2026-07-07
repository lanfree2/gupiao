from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from app.models import NodeStatus, Recommendation, TrackingNode, UserPeriod
from app.services.market_data import add_trading_days, get_close_price


DEFAULT_PERIODS = [
    ("1周", 7),
    ("2周", 14),
    ("1月", 30),
    ("2月", 60),
    ("3月", 90),
]


def ensure_user_periods(db: Session, user_id: int) -> list[UserPeriod]:
    periods = db.query(UserPeriod).filter(UserPeriod.user_id == user_id).order_by(UserPeriod.sort_order).all()
    if periods:
        return periods
    for i, (label, days) in enumerate(DEFAULT_PERIODS):
        db.add(UserPeriod(user_id=user_id, label=label, days=days, sort_order=i))
    db.commit()
    return db.query(UserPeriod).filter(UserPeriod.user_id == user_id).order_by(UserPeriod.sort_order).all()


def create_tracking_nodes(db: Session, rec: Recommendation, periods: list[UserPeriod]) -> None:
    for p in periods:
        due = add_trading_days(rec.recommend_date, p.days)
        db.add(
            TrackingNode(
                recommendation_id=rec.id,
                label=p.label,
                days=p.days,
                due_date=due,
                status=NodeStatus.pending,
            )
        )
    db.commit()


def process_due_nodes(db: Session, as_of: date | None = None) -> dict:
    today = as_of or date.today()
    nodes = (
        db.query(TrackingNode)
        .options(joinedload(TrackingNode.recommendation))
        .filter(TrackingNode.status == NodeStatus.pending, TrackingNode.due_date <= today)
        .all()
    )
    done, failed = 0, 0
    for node in nodes:
        rec = node.recommendation
        close = get_close_price(db, rec.stock_code, today)
        if close is None:
            node.status = NodeStatus.failed
            node.error_message = "无法获取收盘价"
            failed += 1
            continue
        pct = (close - rec.recommend_price) / rec.recommend_price * 100
        node.close_price = close
        node.pct_change = round(pct, 2)
        node.status = NodeStatus.done
        node.fetched_at = datetime.utcnow()
        done += 1
    db.commit()
    return {"processed": len(nodes), "done": done, "failed": failed}
