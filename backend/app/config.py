from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "荐迹"
    env: str = "development"
    secret_key: str = "dev-secret-change-me"
    jwt_expire_hours: int = 168
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "postgresql+psycopg2://jianji:jianji@localhost:5432/jianji"
    redis_url: str = "redis://localhost:6379/0"

    # SMS
    sms_enabled: bool = False
    sms_mock_code: str = "123456"
    sms_code_expire_minutes: int = 10
    sms_send_interval_seconds: int = 60
    sms_provider: str = "mock"
    aliyun_access_key_id: str = ""
    aliyun_access_secret: str = ""
    aliyun_sms_sign_name: str = ""
    aliyun_sms_template_register: str = ""
    aliyun_sms_template_reset_password: str = ""

    # Worker
    market_data_provider: str = "akshare"
    worker_enabled: bool = True
    tracking_cron_hour: int = 16
    tracking_cron_minute: int = 30

    # Seed admin / demo
    admin_phone: str = "13800000000"
    admin_password: str = "admin123"
    admin_nickname: str = "系统管理员"
    seed_demo_user: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
