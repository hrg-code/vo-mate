from functools import lru_cache
from typing import Optional

from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

from app.core.config import get_settings


@lru_cache
def get_admin_engine() -> Optional[Engine]:
    settings = get_settings()
    if not settings.postgres_host:
        return None

    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_database,
    )
    return create_engine(url, pool_pre_ping=True)
