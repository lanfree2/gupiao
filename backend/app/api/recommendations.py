from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import joinedload

from app.deps import CurrentUser, DbSession
from app.models import Channel, NodeStatus, Recommendation, TrackingNode
from app.schemas import (
    ChannelIn,
    ChannelOut,
    ChannelStatsOut,
    FetchResultOut,
    IdIn,
    MessageOut,
    RecommendationCreateOut,
    RecommendationIn,
    RecommendationOut,
    RecommendationUpdateIn,
)
from app.services.market_data import get_close_on_or_before, lookup_stock_name, prefetch_close_prices
from app.services.stats import collect_node_values, rec_to_out, stats_from_values, all_node_values
from app.services.period_calc import due_date_for_user_period
from app.services.tracking import (
    create_tracking_nodes,
    ensure_user_periods,
    process_recommendation_due_nodes,
    rebuild_tracking_nodes,
    reset_recommendation_nodes,
)

router = APIRouter(prefix="/recommendations", tags=["自选"])


def _resolve_recommend_price(db: DbSession, stock_code: str, recommend_date, price: float | None) -> float:
    if price is not None and price > 0:
        return price
    result = get_close_on_or_before(db, stock_code, recommend_date)
    if result:
        return result[0]
    return 0.0


def _try_fill_recommend_price(db: DbSession, rec: Recommendation) -> bool:
    if rec.recommend_price and rec.recommend_price > 0:
        return True
    prefetch_close_prices(db, rec.stock_code, [rec.recommend_date])
    result = get_close_on_or_before(db, rec.stock_code, rec.recommend_date, max_lookback=30)
    if not result:
        return False
    rec.recommend_price = result[0]
    db.commit()
    return True


def _safe_fetch_nodes(db: DbSession, rec_id: int) -> dict:
    import logging

    logger = logging.getLogger(__name__)
    try:
        result = process_recommendation_due_nodes(db, rec_id)
        logger.info("抓取行情 rec=%s result=%s", rec_id, result)
        return result
    except Exception as exc:
        logger.exception("抓取行情失败 rec=%s: %s", rec_id, exc)
        return {"processed": 0, "done": 0, "failed": 0, "error": str(exc)}


def _fetch_result_out(raw: dict) -> FetchResultOut:
    processed = int(raw.get("processed", 0))
    done = int(raw.get("done", 0))
    failed = int(raw.get("failed", 0))
    if raw.get("error"):
        message = f"抓取失败：{raw['error']}"
    elif processed == 0:
        message = "暂无到期节点。若自选日期是今天，需等节点到期；补录历史请选较早日期"
    elif failed:
        message = f"已抓取 {done} 个节点，{failed} 个失败（可能停牌或网络问题）"
    else:
        message = f"已抓取 {done} 个节点行情"
    return FetchResultOut(processed=processed, done=done, failed=failed, message=message)


def _do_delete_recommendation(db: DbSession, rec: Recommendation) -> None:
    db.query(TrackingNode).filter(TrackingNode.recommendation_id == rec.id).delete(
        synchronize_session=False
    )
    db.delete(rec)
    db.commit()


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
    channel_id: int | None = None,
):
    query = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == user.id)
    )
    if channel_id:
        query = query.filter(Recommendation.channel_id == channel_id)
    items = query.all()
    keyword = q.strip()
    if not keyword:
        if scope in ("stock", "channel"):
            return []
        items = sorted(items, key=lambda r: r.recommend_date, reverse=True)
        return [RecommendationOut(**rec_to_out(r)) for r in items]
    ql = keyword.lower()
    result = []
    for r in items:
        code = (r.stock_code or "").lower()
        name = (r.stock_name or "").lower()
        ch = (r.channel.name if r.channel else "").lower()
        if scope == "stock" and (ql in code or ql in name):
            result.append(r)
        elif scope == "channel" and ql in ch:
            result.append(r)
        elif scope == "all" and (ql in code or ql in name or ql in ch):
            result.append(r)
    result.sort(key=lambda r: r.recommend_date, reverse=True)
    return [RecommendationOut(**rec_to_out(r)) for r in result]


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
        vals = collect_node_values(recs, p.label)
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
    all_vals = all_node_values(recs)
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


def _delete_rec_by_id(db: DbSession, rec_id: int, user_id: int) -> MessageOut:
    from app.services.stats import load_recommendation

    rec = load_recommendation(db, rec_id, user_id)
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")
    _do_delete_recommendation(db, rec)
    return MessageOut(message="自选记录已删除")


@router.post("/remove", response_model=MessageOut)
def remove_recommendation_by_id(body: IdIn, user: CurrentUser, db: DbSession):
    """删除推荐（POST /remove，避免部分代理对 delete 路径返回 405）。"""
    return _delete_rec_by_id(db, body.id, user.id)


@router.post("/delete", response_model=MessageOut)
def delete_recommendation_by_id(body: IdIn, user: CurrentUser, db: DbSession):
    return remove_recommendation_by_id(body, user, db)


@router.get("/{rec_id}", response_model=RecommendationOut)
def get_recommendation(rec_id: int, user: CurrentUser, db: DbSession):
    from app.services.stats import load_recommendation

    rec = load_recommendation(db, rec_id, user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")
    return RecommendationOut(**rec_to_out(rec))


@router.post("", response_model=RecommendationCreateOut)
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
    periods = ensure_user_periods(db, user.id)
    due_dates = [due_date_for_user_period(body.recommend_date, p) for p in periods]
    prefetch_close_prices(db, stock_code, [body.recommend_date, *due_dates])
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
    create_tracking_nodes(db, rec, periods)
    if rec.recommend_price <= 0 and _try_fill_recommend_price(db, rec):
        reset_recommendation_nodes(db, rec.id)
    fetch_raw = _safe_fetch_nodes(db, rec.id)
    rec = load_rec(db, rec.id)
    return RecommendationCreateOut(
        recommendation=RecommendationOut(**rec_to_out(rec)),
        fetch=_fetch_result_out(fetch_raw),
    )


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
    return _delete_rec_by_id(db, rec_id, user.id)


@router.post("/{rec_id}/delete", response_model=MessageOut)
def delete_recommendation_post(rec_id: int, user: CurrentUser, db: DbSession):
    return _delete_rec_by_id(db, rec_id, user.id)


@router.post("/{rec_id}/refetch", response_model=FetchResultOut)
def refetch_recommendation(rec_id: int, user: CurrentUser, db: DbSession):
    """重新抓取某条推荐所有已到期节点行情。"""
    from app.services.stats import load_recommendation

    rec = load_recommendation(db, rec_id, user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")
    reset_recommendation_nodes(db, rec_id)
    return _fetch_result_out(_safe_fetch_nodes(db, rec_id))


def load_rec(db, rec_id):
    return (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.id == rec_id)
        .first()
    )
