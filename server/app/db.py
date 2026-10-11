from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    url = get_settings().sqlalchemy_url
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    # Serverless: few short-lived connections, and the database may have been asleep.
    return create_engine(url, pool_size=2, max_overflow=2, pool_pre_ping=True, pool_recycle=300)


def get_db() -> Iterator[Session]:
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session
