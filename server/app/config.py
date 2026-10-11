import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVER_DIR.parent
# Everything personal (seed CSV, statement samples, backups, local DB, .env) lives here.
# The folder is git-ignored and does not exist on the deployed host.
PRIVATE_DIR = REPO_ROOT / "private"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=PRIVATE_DIR / ".env", extra="ignore")

    database_url: str = ""
    app_env: str = "development"
    app_password_hash: str = ""
    session_secret: str = ""
    session_days: int = 30

    @property
    def is_production(self) -> bool:
        return self.app_env == "production" or bool(os.environ.get("VERCEL"))

    @property
    def auth_enabled(self) -> bool:
        return bool(self.app_password_hash)

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if not url:
            if self.is_production:
                raise RuntimeError("DATABASE_URL is not set")
            return f"sqlite:///{(PRIVATE_DIR / 'finance.db').as_posix()}"
        # Hosted Postgres providers hand out postgres:// or postgresql:// URLs.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url

    def validate_for_startup(self) -> None:
        """Fail closed: a deployed app must never come up without a login."""
        if self.is_production and not self.auth_enabled:
            raise RuntimeError("APP_PASSWORD_HASH must be set in production")
        if self.auth_enabled and len(self.session_secret) < 32:
            raise RuntimeError("SESSION_SECRET must be set (32+ characters) when a password is set")


@lru_cache
def get_settings() -> Settings:
    return Settings()
