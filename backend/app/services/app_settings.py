from sqlalchemy.orm import Session

from app.models import AppSetting

REGISTER_SMS_REQUIRED = "register_sms_required"
INVITE_VIEW_USERS = "invite_view_users"
INVITE_VIEW_CHANNELS = "invite_view_channels"


def get_bool(db: Session, key: str, default: bool = False) -> bool:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not row:
        return default
    return row.value.lower() in ("1", "true", "yes", "on")


def set_bool(db: Session, key: str, value: bool) -> None:
    row = db.query(AppSetting).filter(AppSetting.key == key).first()
    val = "true" if value else "false"
    if row:
        row.value = val
    else:
        db.add(AppSetting(key=key, value=val))
    db.commit()


def register_sms_required(db: Session) -> bool:
    return get_bool(db, REGISTER_SMS_REQUIRED, default=False)


def invite_view_users(db: Session) -> bool:
    return get_bool(db, INVITE_VIEW_USERS, default=True)


def invite_view_channels(db: Session) -> bool:
    return get_bool(db, INVITE_VIEW_CHANNELS, default=False)
