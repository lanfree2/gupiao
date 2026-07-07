from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import joinedload

from app.deps import CurrentUser, DbSession
from app.models import Channel, NodeStatus, Recommendation, TrackingNode
from app.schemas import ChannelIn, ChannelOut, ChannelStatsOut, MessageOut, RecommendationIn, RecommendationOut, RecommendationUpdateIn
from app.services.market_data import get_close_on_or_before, lookup_stock_name
from app.services.stats import collect_node_values, rec_to_out, stats_from_values
from app.services.tracking import (
    create_tracking_nodes,
    ensure_user_periods,
    process_recommendation_due_nodes,
    rebuild_tracking_nodes,
)

router = APIRouter(prefix="/recommendations", tags=["推荐"])


def _resolve_recommend_price(db: DbSession, stock_code: str, recommend_date, price: float | None) -> float:
    if price is not None and price > 0:
        return price
    result = get_close_on_or_before(db, stock_code, recommend_date)
    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"未填写价格且无法获取 {recommend_date} 的收盘价，请手动填写或更换日期",
        )
    return result[0]


def _safe_fetch_nodes(db: DbSession, rec_id: int) -> dict:
    try:
        return process_recommendation_due_nodes(db, rec_id)
    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception("抓取行情失败 rec=%s: %s", rec_id, exc)
        return {"processed": 0, "done": 0, "failed": 0, "error": str(exc)}


@router.get("", response_model=list[RecommendationOut])
def list_recommendations(
    user: CurrentUser,
    db: DbSession,
    q: str | None = None,
    channel_id: int | None = None,
):
    query = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.recommend_date.desc())
    )
    if channel_id:
        query = query.filter(Recommendation.channel_id == channel_id)
    if q:
        query = query.filter(
            (Recommendation.stock_code.contains(q)) | (Recommendation.stock_name.contains(q))
        )
    return [RecommendationOut(**rec_to_out(r)) for r in query.all()]


@router.get("/search", response_model=list[RecommendationOut])
def search_recommendations(
    user: CurrentUser,
    db: DbSession,
    q: str = "",
    scope: str = Query("all", pattern="^(all|stock|channel)$"),
):
    query = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == user.id)
    )
    items = query.all()
    if not q:
        return [RecommendationOut(**rec_to_out(r)) for r in items]
    ql = q.lower()
    result = []
    for r in items:
        if scope == "stock" and (q in r.stock_code or q in r.stock_name):
            result.append(r)
        elif scope == "channel" and q in r.channel.name:
            result.append(r)
        elif scope == "all" and (
            q in r.stock_code or q in r.stock_name or q in r.channel.name
        ):
            result.append(r)
    return [RecommendationOut(**rec_to_out(r)) for r in result]


@router.get("/{rec_id}", response_model=RecommendationOut)
def get_recommendation(rec_id: int, user: CurrentUser, db: DbSession):
    from app.services.stats import load_recommendation

    rec = load_recommendation(db, rec_id, user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")
    return RecommendationOut(**rec_to_out(rec))


@router.post("", response_model=RecommendationOut)
def create_recommendation(body: RecommendationIn, user: CurrentUser, db: DbSession):
    channel = None
    if body.channel_id:
        channel = db.query(Channel).filter(Channel.id == body.channel_id, Channel.user_id == user.id).first()
    elif body.new_channel_name:
        name = body.new_channel_name.strip()
        channel = db.query(Channel).filter(Channel.user_id == user.id, Channel.name == name).first()
        if not channel:
            colors = ["blue", "green", "orange", "purple", "gray"]
            count = db.query(Channel).filter(Channel.user_id == user.id).count()
            channel = Channel(
                user_id=user.id,
                name=name,
                color=colors[count % len(colors)],
                description="录入时自动创建",
            )
            db.add(channel)
            db.flush()
    if not channel:
        raise HTTPException(status_code=400, detail="请选择或输入渠道")

    stock_name = body.stock_name or lookup_stock_name(body.stock_code) or "未知"
    stock_code = body.stock_code.strip()
    recommend_price = _resolve_recommend_price(db, stock_code, body.recommend_date, body.recommend_price)
    rec = Recommendation(
        user_id=user.id,
        channel_id=channel.id,
        stock_code=stock_code,
        stock_name=stock_name,
        recommend_date=body.recommend_date,
        recommend_price=recommend_price,
        reason=body.reason,
    )
    db.add(rec)
    db.flush()
    periods = ensure_user_periods(db, user.id)
    create_tracking_nodes(db, rec, periods)
    _safe_fetch_nodes(db, rec.id)
    db.refresh(rec)
    rec = load_rec(db, rec.id)
    return RecommendationOut(**rec_to_out(rec))


@router.put("/{rec_id}", response_model=RecommendationOut)
def update_recommendation(rec_id: int, body: RecommendationUpdateIn, user: CurrentUser, db: DbSession):
    from app.services.stats import load_recommendation

    rec = load_recommendation(db, rec_id, user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")

    changed_tracking = False
    if body.recommend_date is not None and body.recommend_date != rec.recommend_date:
        rec.recommend_date = body.recommend_date
        changed_tracking = True
    if body.recommend_price is not None and body.recommend_price != rec.recommend_price:
        rec.recommend_price = body.recommend_price
        changed_tracking = True
    if body.reason is not None:
        rec.reason = body.reason

    db.commit()
    if changed_tracking:
        rebuild_tracking_nodes(db, rec, user.id)
        _safe_fetch_nodes(db, rec.id)

    rec = load_rec(db, rec_id)
    return RecommendationOut(**rec_to_out(rec))


@router.delete("/{rec_id}", response_model=MessageOut)
def delete_recommendation(rec_id: int, user: CurrentUser, db: DbSession):
    from app.services.stats import load_recommendation

    rec = load_recommendation(db, rec_id, user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.query(TrackingNode).filter(TrackingNode.recommendation_id == rec_id).delete(
        synchronize_session=False
    )
    db.delete(rec)
    db.commit()
    return MessageOut(message="推荐记录已删除")


def load_rec(db, rec_id):
    return (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.id == rec_id)
        .first()
    )


@router.get("/channels/{channel_id}/detail")
def channel_detail(channel_id: int, user: CurrentUser, db: DbSession):
    ch = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == user.id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="渠道不存在")
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == user.id, Recommendation.channel_id == channel_id)
        .order_by(Recommendation.recommend_date.desc())
        .all()
    )
    periods = ensure_user_periods(db, user.id)
    period_stats = []
    for i, p in enumerate(periods):
        vals = collect_node_values(recs, i)
        win_rate, avg = stats_from_values(vals)
        period_stats.append(
            {
                "label": p.label,
                "days": p.days,
                "sample": len(vals),
                "win_rate": win_rate,
                "avg_return": avg,
            }
        )
    all_vals = []
    for r in recs:
        for n in r.nodes:
            if n.status == NodeStatus.done and n.pct_change is not None:
                all_vals.append(n.pct_change)
    win_rate, avg = stats_from_values(all_vals)
    return {
        "channel": ChannelOut.model_validate(ch),
        "stats": {
            "record_count": len(recs),
            "win_rate": win_rate,
            "avg_return": avg,
            "stock_count": len({r.stock_code for r in recs}),
        },
        "period_stats": period_stats,
        "records": [rec_to_out(r) for r in recs],
    }
