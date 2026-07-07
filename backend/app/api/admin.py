from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import joinedload

from app.deps import CurrentAdmin, DbSession
from app.models import Channel, NodeStatus, Recommendation, User, UserPeriod, UserRole
from app.schemas import AdminChannelOut, IdIn, MessageOut, RecommendationOut, StockAggOut
from app.services.stats import all_node_values, collect_node_values, rec_to_out, stats_from_values
from app.services.tracking import ensure_user_periods

router = APIRouter(prefix="/admin", tags=["管理后台"])


@router.get("/dashboard")
def admin_dashboard(db: DbSession, admin: CurrentAdmin):
    users = db.query(User).filter(User.role == UserRole.user).count()
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel), joinedload(Recommendation.user))
        .all()
    )
    stocks = len({r.stock_code for r in recs})
    all_vals = all_node_values(recs)
    win_rate, _ = stats_from_values(all_vals)
    recent = sorted(recs, key=lambda r: r.created_at, reverse=True)[:5]
    return {
        "user_count": users,
        "record_count": len(recs),
        "stock_count": stocks,
        "win_rate": win_rate,
        "recent": [
            {
                **rec_to_out(r),
                "user_nickname": r.user.nickname,
                "user_phone": r.user.phone[-4:].rjust(len(r.user.phone), "*"),
            }
            for r in recent
        ],
    }


@router.get("/stocks", response_model=list[StockAggOut])
def admin_stocks(db: DbSession, admin: CurrentAdmin, q: str | None = None):
    recs = db.query(Recommendation).options(joinedload(Recommendation.nodes)).all()
    sample = db.query(UserPeriod).order_by(UserPeriod.sort_order).first()
    plen = db.query(UserPeriod).filter(UserPeriod.user_id == sample.user_id).count() if sample else 5

    groups: dict[str, list] = {}
    for r in recs:
        if q and q not in r.stock_code and q not in r.stock_name:
            continue
        groups.setdefault(r.stock_code, []).append(r)

    result = []
    for code, items in groups.items():
        users = len({r.user_id for r in items})
        period_avgs = []
        for i in range(plen):
            vals = collect_node_values(items, i)
            _, avg = stats_from_values(vals)
            period_avgs.append(avg)
        result.append(
            StockAggOut(
                stock_code=code,
                stock_name=items[0].stock_name,
                count=len(items),
                user_count=users,
                period_avgs=period_avgs,
            )
        )
    result.sort(key=lambda x: -x.count)
    return result


@router.get("/stocks/{code}")
def admin_stock_detail(code: str, db: DbSession, admin: CurrentAdmin):
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel), joinedload(Recommendation.user))
        .filter(Recommendation.stock_code == code)
        .order_by(Recommendation.recommend_date.desc())
        .all()
    )
    if not recs:
        raise HTTPException(status_code=404, detail="股票不存在")
    all_vals = all_node_values(recs)
    win_rate, avg_return = stats_from_values(all_vals)
    from app.models import UserPeriod

    periods = db.query(UserPeriod).order_by(UserPeriod.user_id, UserPeriod.sort_order).all()
    labels = []
    seen = set()
    for p in periods:
        if p.label not in seen:
            labels.append(p.label)
            seen.add(p.label)
    if not labels:
        labels = ["1周", "2周", "1月", "2月", "3月"]
    period_stats = []
    for i, label in enumerate(labels[:5]):
        vals = collect_node_values(recs, i)
        wr, ar = stats_from_values(vals)
        period_stats.append({"label": label, "sample": len(vals), "win_rate": wr, "avg_return": ar})
    return {
        "stock_code": code,
        "stock_name": recs[0].stock_name,
        "count": len(recs),
        "user_count": len({r.user_id for r in recs}),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "period_stats": period_stats,
        "records": [
            {**rec_to_out(r), "user_nickname": r.user.nickname, "user_id": r.user_id}
            for r in recs
        ],
    }


@router.get("/channels", response_model=list[AdminChannelOut])
def admin_channels(
    db: DbSession,
    admin: CurrentAdmin,
    q: str | None = None,
    user_id: int | None = None,
):
    channels = (
        db.query(Channel)
        .options(joinedload(Channel.user))
        .filter(Channel.is_active.is_(True))
        .all()
    )
    result = []
    for ch in channels:
        if user_id and ch.user_id != user_id:
            continue
        label = f"{ch.user.nickname}{ch.name}"
        if q and q not in label and q not in ch.name:
            continue
        recs = (
            db.query(Recommendation)
            .options(joinedload(Recommendation.nodes))
            .filter(Recommendation.channel_id == ch.id)
            .all()
        )
        vals = all_node_values(recs)
        win_rate, avg = stats_from_values(vals)
        result.append(
            AdminChannelOut(
                user_id=ch.user_id,
                user_nickname=ch.user.nickname,
                channel_id=ch.id,
                name=ch.name,
                color=ch.color,
                description=ch.description,
                record_count=len(recs),
                win_rate=win_rate,
                avg_return=avg,
            )
        )
    result.sort(key=lambda x: -x.record_count)
    return result


@router.get("/channels/{channel_id}")
def admin_channel_detail(channel_id: int, db: DbSession, admin: CurrentAdmin):
    ch = db.query(Channel).options(joinedload(Channel.user)).filter(Channel.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="渠道不存在")
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.channel_id == channel_id)
        .order_by(Recommendation.recommend_date.desc())
        .all()
    )
    periods_meta = db.query(UserPeriod).filter(UserPeriod.user_id == ch.user_id).order_by(UserPeriod.sort_order).all()
    if not periods_meta:
        from app.services.tracking import DEFAULT_PERIODS

        periods_meta = [type("P", (), {"label": l, "days": d})() for l, d in DEFAULT_PERIODS]
    period_stats = []
    for i, p in enumerate(periods_meta):
        vals = collect_node_values(recs, i)
        wr, ar = stats_from_values(vals)
        wins = sum(1 for v in vals if v > 0)
        period_stats.append(
            {
                "label": p.label,
                "sample": len(vals),
                "wins": wins,
                "win_rate": wr,
                "avg_return": ar,
                "max_up": max(vals) if vals else None,
                "max_down": min(vals) if vals else None,
            }
        )
    all_vals = all_node_values(recs)
    win_rate, avg_return = stats_from_values(all_vals)
    return {
        "channel": {
            "id": ch.id,
            "name": ch.name,
            "color": ch.color,
            "description": ch.description,
            "user_id": ch.user_id,
            "user_nickname": ch.user.nickname,
        },
        "stats": {
            "record_count": len(recs),
            "win_rate": win_rate,
            "avg_return": avg_return,
            "stock_count": len({r.stock_code for r in recs}),
        },
        "period_stats": period_stats,
        "records": [
            {**rec_to_out(r), "user_nickname": ch.user.nickname}
            for r in recs
        ],
    }


@router.get("/records", response_model=list[RecommendationOut])
def admin_records(
    db: DbSession,
    admin: CurrentAdmin,
    q: str = "",
    scope: str = Query("all", pattern="^(all|stock|channel|user)$"),
):
    items = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel), joinedload(Recommendation.user))
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    if not q:
        return [RecommendationOut(**rec_to_out(r)) for r in items]
    result = []
    for r in items:
        if scope == "stock" and (q in r.stock_code or q in r.stock_name):
            result.append(r)
        elif scope == "channel" and q in r.channel.name:
            result.append(r)
        elif scope == "user" and (q in r.user.nickname or q in r.user.phone):
            result.append(r)
        elif scope == "all" and (
            q in r.stock_code or q in r.stock_name or q in r.channel.name or q in r.user.nickname
        ):
            result.append(r)
    return [RecommendationOut(**rec_to_out(r)) for r in result]


@router.post("/worker/run")
def trigger_worker(db: DbSession, admin: CurrentAdmin):
    from app.services.tracking import process_due_nodes

    return process_due_nodes(db)


@router.post("/recommendations/{rec_id}/refetch")
def refetch_recommendation(rec_id: int, db: DbSession, admin: CurrentAdmin):
    """重置并重新抓取某条推荐的所有追踪节点。"""
    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(404, "推荐记录不存在")
    from app.services.tracking import process_recommendation_due_nodes, reset_recommendation_nodes

    reset_count = reset_recommendation_nodes(db, rec_id)
    result = process_recommendation_due_nodes(db, rec_id)
    return {"reset_nodes": reset_count, **result}


@router.post("/recommendations/delete", response_model=MessageOut)
def admin_delete_recommendation_by_id(body: IdIn, db: DbSession, admin: CurrentAdmin):
    return admin_delete_recommendation(body.id, db, admin)


@router.delete("/recommendations/{rec_id}", response_model=MessageOut)
def admin_delete_recommendation(rec_id: int, db: DbSession, admin: CurrentAdmin):
    from app.models import TrackingNode

    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(404, "推荐记录不存在")
    db.query(TrackingNode).filter(TrackingNode.recommendation_id == rec_id).delete(
        synchronize_session=False
    )
    db.delete(rec)
    db.commit()
    return MessageOut(message="推荐记录已删除")


@router.post("/recommendations/{rec_id}/delete", response_model=MessageOut)
def admin_delete_recommendation_post(rec_id: int, db: DbSession, admin: CurrentAdmin):
    return admin_delete_recommendation(rec_id, db, admin)
