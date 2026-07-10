from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models import Channel, NodeStatus, Recommendation, TrackingNode, User


def pct_display(v: float | None) -> str:
    if v is None:
        return "—"
    sign = "+" if v > 0 else ""
    return f"{sign}{v:.1f}%"


def node_is_due(n: TrackingNode, as_of: date | None = None) -> bool:
    """到期日已到（含当天）才可展示与统计。"""
    return n.due_date <= (as_of or date.today())


def node_pct_value(n: TrackingNode, as_of: date | None = None) -> float | None:
    if not node_is_due(n, as_of):
        return None
    if n.status == NodeStatus.done and n.pct_change is not None:
        return n.pct_change
    return None


def node_out_fields(n: TrackingNode, as_of: date | None = None) -> dict:
    """API 输出：未到期节点不返回收盘价与涨跌幅。"""
    if not node_is_due(n, as_of):
        return {"status": "pending", "close_price": None, "pct_change": None}
    return {
        "status": n.status.value,
        "close_price": n.close_price,
        "pct_change": n.pct_change if n.status == NodeStatus.done else None,
    }

def sort_nodes(nodes: list[TrackingNode]) -> list[TrackingNode]:
    """表格列等按用户周期配置顺序。"""
    return sorted(nodes, key=lambda n: (n.sort_order, n.due_date, n.id))


def sort_nodes_by_due_date(nodes: list[TrackingNode]) -> list[TrackingNode]:
    """时间线按到期日先后。"""
    return sorted(nodes, key=lambda n: (n.due_date, n.sort_order, n.id))


def find_node_by_label(rec: Recommendation, label: str) -> TrackingNode | None:
    for n in sort_nodes(rec.nodes):
        if n.label == label:
            return n
    return None


def collect_node_values(
    recs: list[Recommendation], period_label: str, as_of: date | None = None
) -> list[float]:
    vals = []
    for r in recs:
        n = find_node_by_label(r, period_label)
        pct = node_pct_value(n, as_of) if n else None
        if pct is not None:
            vals.append(pct)
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


def rec_to_out(rec: Recommendation, as_of: date | None = None) -> dict:
    nodes = sort_nodes(rec.nodes)
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
                "sort_order": n.sort_order,
                "due_date": n.due_date,
                **node_out_fields(n, as_of),
            }
            for n in nodes
        ],
    }

def all_node_values(recs: list[Recommendation], as_of: date | None = None) -> list[float]:
    vals = []
    for r in recs:
        for n in sort_nodes(r.nodes):
            pct = node_pct_value(n, as_of)
            if pct is not None:
                vals.append(pct)
    return vals


def count_due_pending_nodes(recs: list[Recommendation], as_of: date | None = None) -> int:
    """已到期但尚未完成抓取的节点数。"""
    today = as_of or date.today()
    return sum(
        1
        for r in recs
        for n in r.nodes
        if node_is_due(n, today) and n.status != NodeStatus.done
    )