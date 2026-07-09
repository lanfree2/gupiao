import secrets
import string

from sqlalchemy.orm import Session

from app.models import Channel, InviteeNote, Recommendation, User, UserRole


def _random_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def ensure_invite_code(db: Session, user: User) -> str:
    if user.invite_code:
        return user.invite_code
    for _ in range(20):
        code = _random_code()
        exists = db.query(User).filter(User.invite_code == code).first()
        if not exists:
            user.invite_code = code
            db.commit()
            db.refresh(user)
            return code
    raise RuntimeError("无法生成唯一邀请码")


def find_user_by_invite_code(db: Session, invite_code: str | None) -> User | None:
    if not invite_code or not invite_code.strip():
        return None
    return db.query(User).filter(User.invite_code == invite_code.strip().upper()).first()


def mask_phone(phone: str) -> str:
    if len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def get_invitee_note(db: Session, inviter_id: int, invitee_id: int) -> str:
    row = (
        db.query(InviteeNote)
        .filter(InviteeNote.inviter_id == inviter_id, InviteeNote.invitee_id == invitee_id)
        .first()
    )
    return row.note if row else ""


def set_invitee_note(db: Session, inviter_id: int, invitee_id: int, note: str) -> None:
    row = (
        db.query(InviteeNote)
        .filter(InviteeNote.inviter_id == inviter_id, InviteeNote.invitee_id == invitee_id)
        .first()
    )
    if row:
        row.note = note.strip()
    else:
        db.add(InviteeNote(inviter_id=inviter_id, invitee_id=invitee_id, note=note.strip()))
    db.commit()


def invitee_summary(db: Session, inviter_id: int, invitee: User) -> dict:
    rec_count = db.query(Recommendation).filter(Recommendation.user_id == invitee.id).count()
    ch_count = db.query(Channel).filter(Channel.user_id == invitee.id, Channel.is_active.is_(True)).count()
    return {
        "id": invitee.id,
        "nickname": invitee.nickname,
        "phone_masked": mask_phone(invitee.phone),
        "record_count": rec_count,
        "channel_count": ch_count,
        "created_at": invitee.created_at,
        "note": get_invitee_note(db, inviter_id, invitee.id),
    }


def list_invitees(db: Session, inviter_id: int) -> list[dict]:
    users = (
        db.query(User)
        .filter(User.invited_by_id == inviter_id, User.role == UserRole.user)
        .order_by(User.created_at.desc())
        .all()
    )
    return [invitee_summary(db, inviter_id, u) for u in users]


def assert_can_view_invitee(db: Session, inviter_id: int, invitee_id: int) -> User:
    invitee = db.query(User).filter(User.id == invitee_id, User.role == UserRole.user).first()
    if not invitee or invitee.invited_by_id != inviter_id:
        raise PermissionError("无权查看该用户")
    return invitee


def backfill_invite_codes(db: Session) -> int:
    users = db.query(User).filter(User.invite_code.is_(None)).all()
    for u in users:
        ensure_invite_code(db, u)
    return len(users)
