from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, DbSession
from app.models import Channel, Recommendation
from app.schemas import ChannelStatsOut, InviteeOut, InviteInfoOut, RecommendationOut
from app.services.invites import assert_can_view_invitee, ensure_invite_code, list_invitees
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


@router.get("/me", response_model=InviteInfoOut)
def my_invite(user: CurrentUser, db: DbSession):
    code = ensure_invite_code(db, user)
    invitees = list_invitees(db, user.id)
    return InviteInfoOut(
        invite_code=code,
        invite_path=f"/login?tab=register&invite={code}",
        invitee_count=len(invitees),
    )


@router.get("/invitees", response_model=list[InviteeOut])
def my_invitees(user: CurrentUser, db: DbSession):
    return [InviteeOut(**x) for x in list_invitees(db, user.id)]


@router.get("/invitees/{invitee_id}/channels", response_model=list[ChannelStatsOut])
def invitee_channels(invitee_id: int, user: CurrentUser, db: DbSession):
    try:
        invitee = assert_can_view_invitee(db, user.id, invitee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    channels = db.query(Channel).filter(Channel.user_id == invitee.id, Channel.is_active.is_(True)).all()
    return [_channel_stats(db, invitee.id, c) for c in channels]


@router.get("/invitees/{invitee_id}/recommendations", response_model=list[RecommendationOut])
def invitee_recommendations(invitee_id: int, user: CurrentUser, db: DbSession):
    try:
        invitee = assert_can_view_invitee(db, user.id, invitee_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    from sqlalchemy.orm import joinedload

    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.nodes), joinedload(Recommendation.channel))
        .filter(Recommendation.user_id == invitee.id)
        .order_by(Recommendation.recommend_date.desc())
        .all()
    )
    return [RecommendationOut(**rec_to_out(r)) for r in recs]
