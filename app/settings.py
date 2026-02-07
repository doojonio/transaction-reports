from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn


class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    model_config = SettingsConfigDict(
        env_file=".env",
    )


settings = Settings()
