from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
import re


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class SmsConfigOut(BaseModel):
    enabled: bool
    mock_mode: bool
    mock_hint: str | None = None
    provider: str
    register_sms_required: bool = False


class RegisterConfigOut(BaseModel):
    sms_required: bool
    sms: SmsConfigOut


class SmsSendIn(BaseModel):
    phone: str
    purpose: str  # register | reset_password

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1\d{10}", v):
            raise ValueError("手机号格式不正确")
        return v


class RegisterIn(BaseModel):
    phone: str
    code: str = ""
    password: str = Field(min_length=6, max_length=64)
    nickname: str = "用户"
    invite_code: str | None = None

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1\d{10}", v):
            raise ValueError("手机号格式不正确")
        return v


class LoginIn(BaseModel):
    phone: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=64)


class ResetPasswordSmsIn(BaseModel):
    phone: str
    code: str
    new_password: str = Field(min_length=6, max_length=64)

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1\d{10}", v):
            raise ValueError("手机号格式不正确")
        return v


class UserOut(BaseModel):
    id: int
    phone: str
    nickname: str
    role: str
    invite_code: str | None = None

    class Config:
        from_attributes = True


class InviteeOut(BaseModel):
    id: int
    nickname: str
    phone_masked: str
    record_count: int
    channel_count: int
    created_at: datetime
    note: str = ""


class InviteeNoteIn(BaseModel):
    note: str = ""


class InviteConfigOut(BaseModel):
    view_users: bool
    view_channels: bool


class InviteInfoOut(BaseModel):
    invite_code: str
    invite_path: str
    invitee_count: int


class AdminUserOut(BaseModel):
    id: int
    phone: str
    nickname: str
    invite_code: str | None
    inviter_id: int | None
    inviter_nickname: str | None
    invitee_count: int
    can_view_invitee_channels: bool = False
    created_at: datetime


class AdminSettingsOut(BaseModel):
    register_sms_required: bool
    invite_view_users: bool = True


class AdminSettingsIn(BaseModel):
    register_sms_required: bool
    invite_view_users: bool = True


class AdminResetPasswordIn(BaseModel):
    new_password: str = Field(min_length=6, max_length=64)


class InviteeChannelPermIn(BaseModel):
    can_view_invitee_channels: bool


class BindInviterIn(BaseModel):
    inviter_id: int | None = None
    invite_code: str | None = None


from typing import Literal

class PeriodIn(BaseModel):
    label: str
    days: int = Field(gt=0, le=365)
    unit: Literal["trading_day", "natural_week", "natural_month"] = "trading_day"


class PeriodOut(BaseModel):
    id: int
    label: str
    days: int
    unit: str = "trading_day"
    sort_order: int

    class Config:
        from_attributes = True


class ChannelIn(BaseModel):
    name: str
    color: str = "blue"
    description: str = ""


class ChannelOut(BaseModel):
    id: int
    name: str
    color: str
    description: str
    is_active: bool

    class Config:
        from_attributes = True


class ChannelStatsOut(ChannelOut):
    record_count: int = 0
    win_rate: float | None = None
    avg_return: float | None = None


class RecommendationIn(BaseModel):
    stock_code: str
    stock_name: str | None = None
    channel_id: int | None = None
    new_channel_name: str | None = None
    recommend_date: date
    recommend_price: float | None = Field(default=None, gt=0)
    reason: str = ""


class RecommendationUpdateIn(BaseModel):
    recommend_date: date | None = None
    recommend_price: float | None = Field(default=None, gt=0)
    reason: str | None = None


class IdIn(BaseModel):
    id: int


class NodeOut(BaseModel):
    id: int
    label: str
    days: int
    sort_order: int = 0
    due_date: date
    status: str
    close_price: float | None
    pct_change: float | None

    class Config:
        from_attributes = True


class RecommendationOut(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    channel_id: int
    channel_name: str
    channel_color: str
    recommend_date: date
    recommend_price: float
    reason: str
    created_at: datetime
    nodes: list[NodeOut] = []

    class Config:
        from_attributes = True


class DashboardOut(BaseModel):
    tracking_count: int
    win_rate: float | None
    avg_return: float | None
    pending_nodes: int
    channel_win_rates: list[dict]
    channel_avg_returns: list[dict]
    period_stats: list[dict] = []
    channel_period_stats: list[dict] = []
    recent: list[RecommendationOut]


class StockAggOut(BaseModel):
    stock_code: str
    stock_name: str
    count: int
    user_count: int
    period_avgs: list[float | None]


class AdminChannelOut(BaseModel):
    user_id: int
    user_nickname: str
    channel_id: int
    name: str
    color: str
    description: str
    record_count: int
    win_rate: float | None
    avg_return: float | None


class MessageOut(BaseModel):
    message: str


class FetchResultOut(BaseModel):
    processed: int = 0
    done: int = 0
    failed: int = 0
    message: str = ""


class RecommendationCreateOut(BaseModel):
    recommendation: RecommendationOut
    fetch: FetchResultOut
