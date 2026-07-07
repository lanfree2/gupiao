from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from app.models import NodeStatus, Recommendation, TrackingNode, UserPeriod
from app.services.market_data import add_trading_days, get_close_on_or_before


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


def rebuild_tracking_nodes(db: Session, rec: Recommendation, user_id: int) -> None:
    """推荐日期/价格变更后，按当前周期配置重建追踪节点。"""
    db.query(TrackingNode).filter(TrackingNode.recommendation_id == rec.id).delete()
    db.flush()
    periods = ensure_user_periods(db, user_id)
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
        result = get_close_on_or_before(db, rec.stock_code, node.due_date)
        if result is None:
            node.status = NodeStatus.failed
            node.error_message = "无法获取收盘价"
            failed += 1
            continue
        close, _actual_date = result
        pct = (close - rec.recommend_price) / rec.recommend_price * 100
        node.close_price = close
        node.pct_change = round(pct, 2)
        node.status = NodeStatus.done
        node.fetched_at = datetime.utcnow()
        done += 1
    db.commit()
    return {"processed": len(nodes), "done": done, "failed": failed}


def reset_recommendation_nodes(db: Session, recommendation_id: int) -> int:
    """重置某条推荐的所有节点，便于修复后重新抓取。"""
    nodes = db.query(TrackingNode).filter(TrackingNode.recommendation_id == recommendation_id).all()
    for node in nodes:
        node.status = NodeStatus.pending
        node.close_price = None
        node.pct_change = None
        node.fetched_at = None
        node.error_message = None
    db.commit()
    return len(nodes)
