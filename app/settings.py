from pathlib import Path

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    MOCKFILL: bool = False
    PROJECT_ROOT: Path = Path(__file__).parent.parent

    model_config = SettingsConfigDict(
        env_file=".env",
    )


settings = Settings()
