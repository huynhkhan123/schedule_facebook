from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/facebook_group_tool"
    browser_profile_path: Path = Path("./var/browser-profile")
    media_storage_dir: Path = Path("./var/media")
    global_daily_auto_limit: PositiveInt = Field(default=20, le=20)
    default_min_delay_seconds: PositiveInt = 300
    default_max_delay_seconds: PositiveInt = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
