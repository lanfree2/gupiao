from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload

from app.deps import CurrentUser, DbSession
from app.models import Channel, Recommendation
from app.schemas import (
    ChannelStatsOut,
    InviteConfigOut,
    InviteInfoOut,
    InviteeNoteIn,
    InviteeOut,
    MessageOut,
    RecommendationOut,
)
from app.services.app_settings import invite_view_users
from app.services.invites import (
    assert_can_view_invitee,
    can_inviter_view_channels,
    ensure_invite_code,
    list_invitees,
    set_invitee_note,
)
from app.services.stats import all_node_values, rec_to_out, stats_from_values

router = APIRouter(prefix="/invites", tags=["邀请"])


def _channel_stats(db, user_id: int, ch: Channel) -> ChannelStatsOut:
    recs = db.query(Recommendation).filter(Recommendation.user_id == user_id, Recommendation.channel_id == ch.id).all()
    vals = []
    for r in recs:
        vals.extend(all_node_values([r]))
    win_rate, avg = stats_from_values(vals)
    return ChannelStatsOut(
        id=ch.id,
        name=ch.name,
        color=ch.color,
        description=ch.description,
        is_active=ch.is_active,
        record_count=len(recs),
        win_rate=win_rate,
        avg_return=avg,
    )


@router.get("/config", response_model=InviteConfigOut)
def invite_config(user: CurrentUser, db: DbSession):
    can_view = invite_view_users(db) and can_inviter_view_channels(user)
    return InviteConfigOut(
        view_users=can_view,
        view_channels=can_view,
    )


@router.get("/me", response_model=InviteInfoOut)
def my_invite(user: CurrentUser, db: DbSession):
    code = ensure_invite_code(db, user)
    invitees = list_invitees(db, user.id) if invite_view_users(db) else []
    return InviteInfoOut(
        invite_code=code,
        invite_path=f"/login?tab=register&invite={code}",
        invitee_count=len(invitees),
    )


@router.get("/invitees", response_model=list[InviteeOut])
def my_invitees(user: CurrentUser, db: DbSession):
    if not invite_view_users(db):
        raise HTTPException(status_code=403, detail="管理员已关闭查看受邀用户")
    if not can_inviter_view_channels(user):
        raise HTTPException(status_code=403, detail="暂无查看受邀用户的权限，请联系管理员开通")
    return [InviteeOut(**x) for x in list_invitees(db, user.id)]


@router.put("/invitees/{invitee_id}/note", response_model=MessageOut)
def save_invitee_note(invitee_id: int, body: InviteeNoteIn, user: CurrentUser, db: DbSession):
    if not invite_view_users(db):
        raise HTTPException(status_code=403, detail="管理员已关闭查看受邀用户")
    if not can_inviter_view_channels(user):
        raise HTTPException(status_code=403, detail="暂无查看受邀用户的权限，请联系管理员开通")
    try:
        assert_can_view_invitee(db, user.id, invitee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    set_invitee_note(db, user.id, invitee_id, body.note)
    return MessageOut(message="备注已保存")


@router.get("/invitees/{invitee_id}/channels", response_model=list[ChannelStatsOut])
def invitee_channels(invitee_id: int, user: CurrentUser, db: DbSession):
    if not can_inviter_view_channels(user):
        raise HTTPException(status_code=403, detail="暂无查看受邀用户渠道的权限，请联系管理员开通")
    try:
        invitee = assert_can_view_invitee(db, user.id, invitee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    channels = db.query(Channel).filter(Channel.user_id == invitee.id, Channel.is_active.is_(True)).all()
    return [_channel_stats(db, invitee.id, c) for c in channels]


@router.get("/invitees/{invitee_id}/channels/{channel_id}/recommendations", response_model=list[RecommendationOut])
def invitee_channel_recommendations(invitee_id: int, channel_id: int, user: CurrentUser, db: DbSession):
    if not can_inviter_view_channels(user):
        raise HTTPException(status_code=403, detail="暂无查看受邀用户渠道的权限，请联系管理员开通")
    try:
        invitee = assert_can_view_invitee(db, user.id, invitee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    ch = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == invitee.id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="渠道不存在")
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == invitee.id, Recommendation.channel_id == channel_id)
        .order_by(Recommendation.recommend_date.desc())
        .all()
    )
    return [RecommendationOut(**rec_to_out(r)) for r in recs]


@router.get("/invitees/{invitee_id}/recommendations", response_model=list[RecommendationOut])
def invitee_recommendations(invitee_id: int, user: CurrentUser, db: DbSession):
    if not can_inviter_view_channels(user):
        raise HTTPException(status_code=403, detail="暂无查看受邀用户渠道的权限，请联系管理员开通")
    try:
        invitee = assert_can_view_invitee(db, user.id, invitee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == invitee.id)
        .order_by(Recommendation.recommend_date.desc())
        .all()
    )
    return [RecommendationOut(**rec_to_out(r)) for r in recs]
