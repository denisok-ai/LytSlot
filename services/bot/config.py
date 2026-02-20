"""
@file: config.py
@description: Bot settings.
@dependencies: pydantic-settings
@created: 2025-02-19
"""

from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    bot_token: str = ""
    api_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = BotSettings()
