from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import joinedload

from app.deps import CurrentAdmin, DbSession, hash_password
from app.models import Channel, NodeStatus, Recommendation, User, UserPeriod, UserRole
from app.schemas import (
    AdminChannelOut,
    AdminSettingsIn,
    AdminSettingsOut,
    AdminResetPasswordIn,
    AdminUserOut,
    BindInviterIn,
    IdIn,
    InviteeChannelPermIn,
    MessageOut,
    RecommendationOut,
    StockAggOut,
)
from app.services.app_settings import (
    INVITE_VIEW_USERS,
    REGISTER_SMS_REQUIRED,
    invite_view_users,
    register_sms_required,
    set_bool,
)
from app.services.invites import ensure_invite_code, find_user_by_invite_code
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
            vals = collect_node_values(items, p.label)
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
        vals = collect_node_values(recs, label)
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
        from app.services.period_calc import DEFAULT_PERIODS

        periods_meta = [type("P", (), {"label": l, "days": d, "unit": u})() for l, d, u in DEFAULT_PERIODS]
    period_stats = []
    for i, p in enumerate(periods_meta):
        vals = collect_node_values(recs, p.label)
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
        raise HTTPException(404, "自选记录不存在")
    from app.services.tracking import process_recommendation_due_nodes, reset_recommendation_nodes

    reset_count = reset_recommendation_nodes(db, rec_id)
    result = process_recommendation_due_nodes(db, rec_id)
    return {"reset_nodes": reset_count, **result}


@router.post("/recommendations/remove", response_model=MessageOut)
def admin_remove_recommendation_by_id(body: IdIn, db: DbSession, admin: CurrentAdmin):
    return admin_delete_recommendation(body.id, db, admin)


@router.post("/recommendations/delete", response_model=MessageOut)
def admin_delete_recommendation_by_id(body: IdIn, db: DbSession, admin: CurrentAdmin):
    return admin_remove_recommendation_by_id(body, db, admin)


@router.delete("/recommendations/{rec_id}", response_model=MessageOut)
def admin_delete_recommendation(rec_id: int, db: DbSession, admin: CurrentAdmin):
    from app.models import TrackingNode

    rec = db.query(Recommendation).filter(Recommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(404, "自选记录不存在")
    db.query(TrackingNode).filter(TrackingNode.recommendation_id == rec_id).delete(
        synchronize_session=False
    )
    db.delete(rec)
    db.commit()
    return MessageOut(message="自选记录已删除")


@router.post("/recommendations/{rec_id}/delete", response_model=MessageOut)
def admin_delete_recommendation_post(rec_id: int, db: DbSession, admin: CurrentAdmin):
    return admin_delete_recommendation(rec_id, db, admin)


@router.get("/users", response_model=list[AdminUserOut])
def admin_users(db: DbSession, admin: CurrentAdmin, q: str = ""):
    users = (
        db.query(User)
        .options(joinedload(User.inviter))
        .filter(User.role == UserRole.user)
        .order_by(User.created_at.desc())
        .all()
    )
    ql = q.strip().lower()
    result = []
    for u in users:
        ensure_invite_code(db, u)
        inviter = u.inviter
        if ql:
            matched = ql in u.phone.lower() or ql in u.nickname.lower()
            if u.invite_code and ql in u.invite_code.lower():
                matched = True
            if inviter and (ql in inviter.nickname.lower() or ql in inviter.phone):
                matched = True
            if not matched:
                continue
        invitee_count = db.query(User).filter(User.invited_by_id == u.id).count()
        result.append(
            AdminUserOut(
                id=u.id,
                phone=u.phone,
                nickname=u.nickname,
                invite_code=u.invite_code,
                inviter_id=inviter.id if inviter else None,
                inviter_nickname=inviter.nickname if inviter else None,
                invitee_count=invitee_count,
                can_view_invitee_channels=bool(u.can_view_invitee_channels),
                created_at=u.created_at,
            )
        )
    return result


@router.put("/users/{user_id}/inviter", response_model=MessageOut)
def admin_bind_inviter(user_id: int, body: BindInviterIn, db: DbSession, admin: CurrentAdmin):
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.user).first()
    if not user:
        raise HTTPException(404, "用户不存在")

    if body.inviter_id is None and not body.invite_code:
        user.invited_by_id = None
        db.commit()
        return MessageOut(message="已解除邀请关系")

    inviter = None
    if body.inviter_id is not None:
        inviter = db.query(User).filter(User.id == body.inviter_id).first()
    elif body.invite_code:
        inviter = find_user_by_invite_code(db, body.invite_code)

    if not inviter:
        raise HTTPException(400, detail="邀请人不存在")
    if inviter.id == user.id:
        raise HTTPException(400, detail="不能邀请自己")
    if inviter.role != UserRole.user and inviter.role != UserRole.admin:
        raise HTTPException(400, detail="邀请人无效")

    user.invited_by_id = inviter.id
    db.commit()
    return MessageOut(message=f"已绑定邀请人：{inviter.nickname}")


@router.put("/users/{user_id}/invitee-channels", response_model=MessageOut)
def admin_set_invitee_channel_perm(user_id: int, body: InviteeChannelPermIn, db: DbSession, admin: CurrentAdmin):
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.user).first()
    if not user:
        raise HTTPException(404, detail="用户不存在")
    user.can_view_invitee_channels = body.can_view_invitee_channels
    db.commit()
    if body.can_view_invitee_channels:
        return MessageOut(message=f"已开通「{user.nickname}」查看受邀用户权限")
    return MessageOut(message=f"已关闭「{user.nickname}」查看受邀用户权限")


@router.put("/users/{user_id}/password", response_model=MessageOut)
def admin_reset_user_password(user_id: int, body: AdminResetPasswordIn, db: DbSession, admin: CurrentAdmin):
    """管理员重置普通用户密码（短信找回关闭时使用）。"""
    user = db.query(User).filter(User.id == user_id, User.role == UserRole.user).first()
    if not user:
        raise HTTPException(404, detail="用户不存在")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return MessageOut(message=f"已重置「{user.nickname}」的登录密码")


@router.get("/settings", response_model=AdminSettingsOut)
def admin_get_settings(db: DbSession, admin: CurrentAdmin):
    return AdminSettingsOut(
        register_sms_required=register_sms_required(db),
        invite_view_users=invite_view_users(db),
    )


@router.put("/settings", response_model=AdminSettingsOut)
def admin_update_settings(body: AdminSettingsIn, db: DbSession, admin: CurrentAdmin):
    set_bool(db, REGISTER_SMS_REQUIRED, body.register_sms_required)
    set_bool(db, INVITE_VIEW_USERS, body.invite_view_users)
    return AdminSettingsOut(
        register_sms_required=body.register_sms_required,
        invite_view_users=body.invite_view_users,
    )
