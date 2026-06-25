"""SQLAlchemy ORM 모델 — Holdings, Transactions, DailySnapshot"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Holding(Base):
    """보유 종목"""
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0.0)
    avg_price = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transaction(Base):
    """매수/매도 거래 이력"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    action = Column(String(10), nullable=False)   # buy / sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    reason = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class DailySnapshot(Base):
    """일별 포트폴리오 가치 스냅샷"""
    __tablename__ = "daily_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, default=date.today, index=True)
    total_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    holdings_value = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0)
    daily_pnl_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class CashBalance(Base):
    """현금 잔고"""
    __tablename__ = "cash_balance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    balance = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
