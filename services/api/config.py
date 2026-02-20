"""
@file: config.py
@description: API settings (env-based).
@dependencies: pydantic-settings
@created: 2025-02-19
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url_sync: str = "postgresql://lytslot:lytslot@localhost:5432/lytslot"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = Field(default="", validation_alias="CELERY_BROKER_URL")
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    telegram_bot_token: str = Field(default="", validation_alias="BOT_TOKEN")
    auth_date_max_age_seconds: int = 86400  # 24 ч — защита от повторного использования init_data
    rate_limit_per_minute: int = 100
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    enable_dev_login: bool = Field(default=False, validation_alias="ENABLE_DEV_LOGIN")
    admin_telegram_ids: str = Field(default="", validation_alias="ADMIN_TELEGRAM_IDS")

    def get_admin_telegram_ids(self) -> list[int]:
        """Список telegram_id админов из ADMIN_TELEGRAM_IDS (через запятую)."""
        if not self.admin_telegram_ids or not self.admin_telegram_ids.strip():
            return []
        return [int(x.strip()) for x in self.admin_telegram_ids.strip().split(",") if x.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
