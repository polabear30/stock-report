"""SQLite 데이터베이스 연결 및 세션 관리"""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_store")
_DB_PATH = os.path.join(_DB_DIR, "portfolio.db")


@lru_cache
def get_engine():
    os.makedirs(_DB_DIR, exist_ok=True)
    engine = create_engine(f"sqlite:///{_DB_PATH}", echo=False)
    return engine


def get_session() -> Session:
    engine = get_engine()
    _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal()


def init_db():
    """테이블이 없으면 생성한다."""
    from portfolio.models import Base
    engine = get_engine()
    Base.metadata.create_all(engine)
