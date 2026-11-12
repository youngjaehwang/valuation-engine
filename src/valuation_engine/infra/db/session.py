# valuation_engine/infra/db/session.py
from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session, sessionmaker

from valuation_engine.infra.db.engine import engine


SessionFactory = Callable[[], Session]

_sessionmaker = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_session() -> Session:
    return _sessionmaker()
