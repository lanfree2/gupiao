import enum
from datetime import datetime, date

from sqlalchemy import (
    String, Boolean, DateTime, Date, ForeignKey, Text, Integer, Float, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class SmsPurpose(str, enum.Enum):
    register = "register"
    reset_password = "reset_password"


class NodeStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(11), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(64), default="用户")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    periods: Mapped[list["UserPeriod"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    channels: Mapped[list["Channel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class SmsCode(Base):
    __tablename__ = "sms_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(11), index=True)
    code: Mapped[str] = mapped_column(String(8))
    purpose: Mapped[SmsPurpose] = mapped_column(Enum(SmsPurpose))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserPeriod(Base):
    __tablename__ = "user_periods"
    __table_args__ = (UniqueConstraint("user_id", "sort_order", name="uq_user_period_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(32))
    days: Mapped[int] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="periods")


class Channel(Base):
    __tablename__ = "channels"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_channel_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    color: Mapped[str] = mapped_column(String(16), default="blue")
    description: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="channels")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="channel")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="RESTRICT"), index=True)
    stock_code: Mapped[str] = mapped_column(String(10), index=True)
    stock_name: Mapped[str] = mapped_column(String(64))
    recommend_date: Mapped[date] = mapped_column(Date)
    recommend_price: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="recommendations")
    channel: Mapped["Channel"] = relationship(back_populates="recommendations")
    nodes: Mapped[list["TrackingNode"]] = relationship(back_populates="recommendation", cascade="all, delete-orphan")


class TrackingNode(Base):
    __tablename__ = "tracking_nodes"
    __table_args__ = (Index("ix_node_due_status", "due_date", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(32))
    days: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[NodeStatus] = mapped_column(Enum(NodeStatus), default=NodeStatus.pending)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    recommendation: Mapped["Recommendation"] = relationship(back_populates="nodes")


class PriceCache(Base):
    __tablename__ = "price_cache"
    __table_args__ = (UniqueConstraint("stock_code", "trade_date", name="uq_price_cache"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(10), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    close_price: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(32), default="akshare")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
