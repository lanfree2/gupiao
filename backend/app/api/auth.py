from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DbSession, create_access_token, hash_password, verify_password
from app.models import SmsPurpose, User, UserRole
from app.schemas import (
    ChangePasswordIn,
    LoginIn,
    MessageOut,
    RegisterConfigOut,
    RegisterIn,
    ResetPasswordSmsIn,
    SmsConfigOut,
    SmsSendIn,
    TokenOut,
    UserOut,
)
from app.services.app_settings import register_sms_required
from app.services.invites import ensure_invite_code, find_user_by_invite_code
from app.services.sms import send_sms_code, sms_config, verify_sms_code
from app.services.tracking import ensure_user_periods

router = APIRouter(prefix="/auth", tags=["认证"])


def _sms_config_out(db) -> SmsConfigOut:
    cfg = sms_config()
    cfg["register_sms_required"] = register_sms_required(db)
    return SmsConfigOut(**cfg)


@router.get("/sms/config", response_model=SmsConfigOut)
def get_sms_config(db: DbSession):
    return _sms_config_out(db)


@router.get("/register/config", response_model=RegisterConfigOut)
def get_register_config(db: DbSession):
    return RegisterConfigOut(sms_required=register_sms_required(db), sms=_sms_config_out(db))


@router.post("/sms/send")
def send_sms(body: SmsSendIn, db: DbSession):
    if body.purpose not in ("register", "reset_password"):
        raise HTTPException(status_code=400, detail="无效的 purpose")
    purpose = SmsPurpose.register if body.purpose == "register" else SmsPurpose.reset_password
    if purpose == SmsPurpose.register:
        exists = db.query(User).filter(User.phone == body.phone).first()
        if exists:
            raise HTTPException(status_code=400, detail="手机号已注册")
    if purpose == SmsPurpose.reset_password:
        exists = db.query(User).filter(User.phone == body.phone).first()
        if not exists:
            raise HTTPException(status_code=404, detail="手机号未注册")
    result = send_sms_code(db, body.phone, purpose)
    if not result.get("ok"):
        raise HTTPException(status_code=429, detail=result.get("message"))
    return result


@router.post("/register", response_model=TokenOut)
def register(body: RegisterIn, db: DbSession):
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(status_code=400, detail="手机号已注册")

    sms_required = register_sms_required(db)
    if sms_required:
        if not body.code or len(body.code.strip()) != 6:
            raise HTTPException(status_code=400, detail="请输入 6 位验证码")
        if not verify_sms_code(db, body.phone, SmsPurpose.register, body.code.strip()):
            raise HTTPException(status_code=400, detail="验证码错误或已过期")
    elif body.code and body.code.strip():
        if not verify_sms_code(db, body.phone, SmsPurpose.register, body.code.strip()):
            raise HTTPException(status_code=400, detail="验证码错误或已过期")

    inviter = find_user_by_invite_code(db, body.invite_code)
    if body.invite_code and body.invite_code.strip() and not inviter:
        raise HTTPException(status_code=400, detail="邀请码无效")

    user = User(
        phone=body.phone,
        password_hash=hash_password(body.password),
        nickname=body.nickname or "用户",
        role=UserRole.user,
        invited_by_id=inviter.id if inviter else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    ensure_user_periods(db, user.id)
    ensure_invite_code(db, user)
    token = create_access_token(user.id, user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: DbSession):
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="手机号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已禁用")
    ensure_invite_code(db, user)
    token = create_access_token(user.id, user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/password/change", response_model=MessageOut)
def change_password(body: ChangePasswordIn, user: CurrentUser, db: DbSession):
    """登录后修改密码：需提供旧密码。"""
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if body.old_password == body.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return MessageOut(message="密码已修改")


@router.post("/password/reset/sms", response_model=MessageOut)
def reset_password_sms(body: ResetPasswordSmsIn, db: DbSession):
    """忘记密码：短信验证码重置。"""
    user = db.query(User).filter(User.phone == body.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="手机号未注册")
    if not verify_sms_code(db, body.phone, SmsPurpose.reset_password, body.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return MessageOut(message="密码已重置，请使用新密码登录")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser, db: DbSession):
    ensure_invite_code(db, user)
    return UserOut.model_validate(user)
