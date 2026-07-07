"""数据库种子：管理员账号 + 演示用户（仅 development）。"""
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.deps import hash_password
from app.models import Channel, User, UserRole
from app.services.tracking import DEFAULT_PERIODS, ensure_user_periods

settings = get_settings()


def run_seed() -> None:
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.phone == settings.admin_phone).first()
        if not admin:
            admin = User(
                phone=settings.admin_phone,
                password_hash=hash_password(settings.admin_password),
                nickname=settings.admin_nickname,
                role=UserRole.admin,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            ensure_user_periods(db, admin.id)

        demo_phone = "13888888888"
        demo = db.query(User).filter(User.phone == demo_phone).first()
        if not demo and settings.seed_demo_user:
            demo = User(
                phone=demo_phone,
                password_hash=hash_password("demo123456"),
                nickname="李先生",
                role=UserRole.user,
            )
            db.add(demo)
            db.commit()
            db.refresh(demo)
            ensure_user_periods(db, demo.id)
            for name, color, desc in [
                ("微信群 A", "blue", "某投资交流群"),
                ("研报订阅", "green", "券商月度研报"),
                ("朋友推荐", "orange", "私人好友分享"),
                ("公众号", "purple", "财经公众号"),
            ]:
                if not db.query(Channel).filter(Channel.user_id == demo.id, Channel.name == name).first():
                    db.add(Channel(user_id=demo.id, name=name, color=color, description=desc))
            db.commit()
    finally:
        db.close()
