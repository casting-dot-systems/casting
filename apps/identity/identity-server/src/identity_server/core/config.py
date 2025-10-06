from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Single postgres database URL (contains both catalog schema and identity tables)
    DATABASE_URL: str = Field(default="postgresql://localhost:5432/cast")

    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="info")


settings = Settings()
