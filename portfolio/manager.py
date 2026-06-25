"""포트폴리오 CRUD 및 수익률 계산"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import desc

from config.settings import get_settings
from portfolio.db import get_session, init_db
from portfolio.models import CashBalance, DailySnapshot, Holding, Transaction


class PortfolioManager:
    """포트폴리오 매수/매도, 현황 조회, 스냅샷 관리"""

    def __init__(self):
        init_db()
        self._ensure_cash_row()

    def _ensure_cash_row(self):
        session = get_session()
        try:
            row = session.query(CashBalance).first()
            if row is None:
                initial = get_settings().initial_cash
                session.add(CashBalance(balance=initial))
                session.commit()
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 거래 기록
    # ------------------------------------------------------------------
    def record_transaction(
        self,
        ticker: str,
        action: str,
        quantity: float,
        price: float,
        reason: str = "",
    ) -> Transaction:
        session = get_session()
        try:
            total = quantity * price
            tx = Transaction(
                ticker=ticker.upper(),
                action=action,
                quantity=quantity,
                price=price,
                total_amount=total,
                reason=reason,
            )
            session.add(tx)

            # 보유 종목 업데이트
            holding = session.query(Holding).filter_by(ticker=ticker.upper()).first()

            if action == "buy":
                self._update_cash(session, -total)
                if holding is None:
                    holding = Holding(ticker=ticker.upper(), quantity=quantity, avg_price=price)
                    session.add(holding)
                else:
                    new_qty = holding.quantity + quantity
                    holding.avg_price = (
                        (holding.avg_price * holding.quantity + price * quantity) / new_qty
                    )
                    holding.quantity = new_qty

            elif action == "sell":
                self._update_cash(session, total)
                if holding and holding.quantity >= quantity:
                    holding.quantity -= quantity
                    if holding.quantity <= 0:
                        session.delete(holding)

            session.commit()
            session.refresh(tx)
            return tx
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 현황 조회
    # ------------------------------------------------------------------
    def get_holdings(self) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            rows = session.query(Holding).filter(Holding.quantity > 0).all()
            return [
                {
                    "ticker": h.ticker,
                    "quantity": h.quantity,
                    "avg_price": round(h.avg_price, 2),
                }
                for h in rows
            ]
        finally:
            session.close()

    def get_cash(self) -> float:
        session = get_session()
        try:
            row = session.query(CashBalance).first()
            return row.balance if row else 0.0
        finally:
            session.close()

    def get_status_summary(self) -> Dict[str, Any]:
        holdings = self.get_holdings()
        cash = self.get_cash()
        holdings_value = sum(h["quantity"] * h["avg_price"] for h in holdings)
        total = cash + holdings_value
        return {
            "cash": round(cash, 2),
            "holdings": holdings,
            "holdings_value": round(holdings_value, 2),
            "total_value": round(total, 2),
        }

    def get_recent_transactions(self, limit: int = 20) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            rows = (
                session.query(Transaction)
                .order_by(desc(Transaction.created_at))
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": t.id,
                    "ticker": t.ticker,
                    "action": t.action,
                    "quantity": t.quantity,
                    "price": t.price,
                    "total_amount": t.total_amount,
                    "reason": t.reason,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in rows
            ]
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 일별 스냅샷
    # ------------------------------------------------------------------
    def take_snapshot(self, holdings_market_value: Optional[float] = None) -> DailySnapshot:
        """오늘의 포트폴리오 가치를 스냅샷으로 저장한다."""
        session = get_session()
        try:
            cash = self.get_cash()
            h_val = holdings_market_value if holdings_market_value is not None else sum(
                h["quantity"] * h["avg_price"] for h in self.get_holdings()
            )
            total = cash + h_val

            prev = (
                session.query(DailySnapshot)
                .order_by(desc(DailySnapshot.snapshot_date))
                .first()
            )
            daily_pnl = total - prev.total_value if prev else 0.0
            daily_pnl_pct = (daily_pnl / prev.total_value * 100) if prev and prev.total_value else 0.0

            snap = DailySnapshot(
                snapshot_date=date.today(),
                total_value=total,
                cash=cash,
                holdings_value=h_val,
                daily_pnl=round(daily_pnl, 2),
                daily_pnl_pct=round(daily_pnl_pct, 2),
            )
            session.add(snap)
            session.commit()
            session.refresh(snap)
            return snap
        finally:
            session.close()

    def get_snapshots(self, limit: int = 60) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            rows = (
                session.query(DailySnapshot)
                .order_by(desc(DailySnapshot.snapshot_date))
                .limit(limit)
                .all()
            )
            return [
                {
                    "date": s.snapshot_date.isoformat(),
                    "total_value": s.total_value,
                    "cash": s.cash,
                    "holdings_value": s.holdings_value,
                    "daily_pnl": s.daily_pnl,
                    "daily_pnl_pct": s.daily_pnl_pct,
                }
                for s in reversed(rows)
            ]
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------
    @staticmethod
    def _update_cash(session, amount: float):
        row = session.query(CashBalance).first()
        if row:
            row.balance += amount
