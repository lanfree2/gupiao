import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import SmsCode, SmsPurpose

settings = get_settings()


def sms_config() -> dict:
    mock_hint = None
    if not settings.sms_enabled and settings.env != "production":
        mock_hint = "演示模式：验证码固定为 " + settings.sms_mock_code
    return {
        "enabled": settings.sms_enabled,
        "mock_mode": not settings.sms_enabled,
        "mock_hint": mock_hint,
        "provider": settings.sms_provider,
    }


def _generate_code() -> str:
    if not settings.sms_enabled:
        return settings.sms_mock_code
    return "".join(random.choices(string.digits, k=6))


def send_sms_code(db: Session, phone: str, purpose: SmsPurpose) -> dict:
    recent = (
        db.query(SmsCode)
        .filter(SmsCode.phone == phone, SmsCode.purpose == purpose, SmsCode.used.is_(False))
        .order_by(SmsCode.created_at.desc())
        .first()
    )
    if recent:
        elapsed = (datetime.utcnow() - recent.created_at).total_seconds()
        if elapsed < settings.sms_send_interval_seconds:
            wait = int(settings.sms_send_interval_seconds - elapsed)
            return {"ok": False, "message": f"请 {wait} 秒后再试", "retry_after": wait}

    code = _generate_code()
    expires = datetime.utcnow() + timedelta(minutes=settings.sms_code_expire_minutes)
    db.add(SmsCode(phone=phone, code=code, purpose=purpose, expires_at=expires))
    db.commit()

    if settings.sms_enabled and settings.sms_provider == "aliyun":
        _send_aliyun(phone, code, purpose)

    msg = "验证码已发送"
    if not settings.sms_enabled:
        msg = f"演示模式：验证码为 {code}"
    return {"ok": True, "message": msg, **sms_config()}


def verify_sms_code(db: Session, phone: str, purpose: SmsPurpose, code: str) -> bool:
    if not settings.sms_enabled and code == settings.sms_mock_code:
        return True
    row = (
        db.query(SmsCode)
        .filter(
            SmsCode.phone == phone,
            SmsCode.purpose == purpose,
            SmsCode.used.is_(False),
            SmsCode.code == code,
        )
        .order_by(SmsCode.created_at.desc())
        .first()
    )
    if not row or row.expires_at < datetime.utcnow():
        return False
    row.used = True
    db.commit()
    return True


def _send_aliyun(phone: str, code: str, purpose: SmsPurpose) -> None:
    """阿里云短信：配置 SMS_ENABLED=true 后填写密钥即可生效。"""
    if not settings.aliyun_access_key_id:
        raise RuntimeError("SMS_ENABLED=true 但未配置 ALIYUN_ACCESS_KEY_ID")
    # 预留接入点：可安装 alibabacloud_dysmsapi20170525
    # template = settings.aliyun_sms_template_register if purpose == SmsPurpose.register else settings.aliyun_sms_template_reset_password
    raise NotImplementedError("请配置阿里云短信 SDK 或保持 SMS_ENABLED=false 使用演示模式")
