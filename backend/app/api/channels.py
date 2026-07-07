from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, DbSession
from app.models import Channel, Recommendation
from app.schemas import ChannelIn, ChannelOut, ChannelStatsOut, MessageOut
from app.services.stats import all_node_values, stats_from_values

router = APIRouter(prefix="/channels", tags=["渠道"])


def _channel_stats(db, user_id: int, ch: Channel) -> ChannelStatsOut:
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user_id, Recommendation.channel_id == ch.id)
        .all()
    )
    for r in recs:
        r.nodes  # noqa: trigger lazy if needed
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


@router.get("", response_model=list[ChannelStatsOut])
def list_channels(user: CurrentUser, db: DbSession):
    channels = db.query(Channel).filter(Channel.user_id == user.id, Channel.is_active.is_(True)).all()
    return [_channel_stats(db, user.id, c) for c in channels]


@router.post("", response_model=ChannelOut)
def create_channel(body: ChannelIn, user: CurrentUser, db: DbSession):
    if db.query(Channel).filter(Channel.user_id == user.id, Channel.name == body.name).first():
        raise HTTPException(status_code=400, detail="渠道名称已存在")
    ch = Channel(user_id=user.id, name=body.name, color=body.color, description=body.description)
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ChannelOut.model_validate(ch)


@router.put("/{channel_id}", response_model=ChannelOut)
def update_channel(channel_id: int, body: ChannelIn, user: CurrentUser, db: DbSession):
    ch = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == user.id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="渠道不存在")
    dup = (
        db.query(Channel)
        .filter(Channel.user_id == user.id, Channel.name == body.name, Channel.id != channel_id)
        .first()
    )
    if dup:
        raise HTTPException(status_code=400, detail="渠道名称已存在")
    ch.name = body.name
    ch.color = body.color
    ch.description = body.description
    db.commit()
    db.refresh(ch)
    return ChannelOut.model_validate(ch)


@router.get("/{channel_id}", response_model=ChannelStatsOut)
def get_channel(channel_id: int, user: CurrentUser, db: DbSession):
    ch = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == user.id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="渠道不存在")
    return _channel_stats(db, user.id, ch)


@router.delete("/{channel_id}", response_model=MessageOut)
def deactivate_channel(channel_id: int, user: CurrentUser, db: DbSession):
    ch = db.query(Channel).filter(Channel.id == channel_id, Channel.user_id == user.id).first()
    if not ch:
        raise HTTPException(status_code=404, detail="渠道不存在")
    ch.is_active = False
    db.commit()
    return MessageOut(message="渠道已停用")
