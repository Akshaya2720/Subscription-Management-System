"""Application configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    # Database
    DATABASE_URL: str = "postgresql://verisub_user:verisub_password@localhost:5432/verisub_db"
    DATABASE_URL_TEST: str = "sqlite:///./test.db"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-secure-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "VERISUB"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # SMTP (optional - leave empty for dev mode)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def smtp_configured(self) -> bool:
        """Return True if SMTP_HOST is configured, False otherwise."""
        return bool(self.SMTP_HOST and self.SMTP_HOST.strip())


settings = Settings()
