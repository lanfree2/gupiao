from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from app.models import NodeStatus, Recommendation, TrackingNode, UserPeriod
from app.services.market_data import get_close_on_or_before, prefetch_close_prices
from app.services.period_calc import DEFAULT_PERIODS, due_date_for_user_period


def ensure_user_periods(db: Session, user_id: int) -> list[UserPeriod]:
    periods = db.query(UserPeriod).filter(UserPeriod.user_id == user_id).order_by(UserPeriod.sort_order).all()
    if periods:
        return periods
    for i, (label, days, unit) in enumerate(DEFAULT_PERIODS):
        db.add(UserPeriod(user_id=user_id, label=label, days=days, unit=unit, sort_order=i))
    db.commit()
    return db.query(UserPeriod).filter(UserPeriod.user_id == user_id).order_by(UserPeriod.sort_order).all()


def create_tracking_nodes(db: Session, rec: Recommendation, periods: list[UserPeriod]) -> None:
    for p in periods:
        due = due_date_for_user_period(rec.recommend_date, p)
        db.add(
            TrackingNode(
                recommendation_id=rec.id,
                label=p.label,
                days=p.days,
                sort_order=p.sort_order,
                due_date=due,
                status=NodeStatus.pending,
            )
        )
    db.commit()


def rebuild_tracking_nodes(db: Session, rec: Recommendation, user_id: int) -> None:
    """自选日期/价格变更后，按当前周期配置重建追踪节点。"""
    db.query(TrackingNode).filter(TrackingNode.recommendation_id == rec.id).delete()
    db.flush()
    periods = ensure_user_periods(db, user_id)
    for p in periods:
        due = due_date_for_user_period(rec.recommend_date, p)
        db.add(
            TrackingNode(
                recommendation_id=rec.id,
                label=p.label,
                days=p.days,
                sort_order=p.sort_order,
                due_date=due,
                status=NodeStatus.pending,
            )
        )
    db.commit()


def _apply_node_price(db: Session, node: TrackingNode) -> bool:
    rec = node.recommendation
    if not rec.recommend_price or rec.recommend_price <= 0:
        node.status = NodeStatus.failed
        node.error_message = "自选价无效"
        return False
    result = get_close_on_or_before(db, rec.stock_code, node.due_date)
    if result is None:
        node.status = NodeStatus.failed
        node.error_message = "无法获取收盘价"
        return False
    close, _actual_date = result
    pct = (close - rec.recommend_price) / rec.recommend_price * 100
    node.close_price = close
    node.pct_change = round(pct, 2)
    node.status = NodeStatus.done
    node.fetched_at = datetime.utcnow()
    return True


def _fetch_pending_nodes(db: Session, nodes: list[TrackingNode]) -> dict:
    done, failed = 0, 0
    for node in sorted(nodes, key=lambda n: (n.sort_order, n.due_date, n.id)):
        if _apply_node_price(db, node):
            done += 1
        else:
            failed += 1
    db.commit()
    return {"processed": len(nodes), "done": done, "failed": failed}


def process_due_nodes(db: Session, as_of: date | None = None) -> dict:
    today = as_of or date.today()
    nodes = (
        db.query(TrackingNode)
        .options(joinedload(TrackingNode.recommendation))
        .filter(
            TrackingNode.status.in_([NodeStatus.pending, NodeStatus.failed]),
            TrackingNode.due_date <= today,
        )
        .all()
    )
    if not nodes:
        return {"processed": 0, "done": 0, "failed": 0}
    by_stock: dict[str, list[date]] = {}
    for node in nodes:
        code = node.recommendation.stock_code
        by_stock.setdefault(code, []).append(node.due_date)
    for code, dates in by_stock.items():
        prefetch_close_prices(db, code, dates)
    return _fetch_pending_nodes(db, nodes)


def process_recommendation_due_nodes(
    db: Session, recommendation_id: int, as_of: date | None = None
) -> dict:
    """抓取某条自选所有已到期节点的历史收盘价。"""
    today = as_of or date.today()
    nodes = (
        db.query(TrackingNode)
        .options(joinedload(TrackingNode.recommendation))
        .filter(
            TrackingNode.recommendation_id == recommendation_id,
            TrackingNode.status.in_([NodeStatus.pending, NodeStatus.failed]),
            TrackingNode.due_date <= today,
        )
        .all()
    )
    if not nodes:
        return {"processed": 0, "done": 0, "failed": 0}
    rec = nodes[0].recommendation
    prefetch_close_prices(db, rec.stock_code, [n.due_date for n in nodes])
    return _fetch_pending_nodes(db, nodes)


def reset_recommendation_nodes(db: Session, recommendation_id: int) -> int:
    """重置某条自选的所有节点，便于修复后重新抓取。"""
    nodes = db.query(TrackingNode).filter(TrackingNode.recommendation_id == recommendation_id).all()
    for node in nodes:
        node.status = NodeStatus.pending
        node.close_price = None
        node.pct_change = None
        node.fetched_at = None
        node.error_message = None
    db.commit()
    return len(nodes)
