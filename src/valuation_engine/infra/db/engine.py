from sqlalchemy import create_engine

from valuation_engine.infra.config.settings import settings

engine = create_engine(
    settings.DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)
