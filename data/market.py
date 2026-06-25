"""Polygon.io REST API를 통한 미국 주식 시장 데이터 수집"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from polygon import RESTClient

from config.settings import get_settings


class MarketDataClient:
    """Polygon.io 기반 주가 데이터 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or get_settings().polygon_api_key
        self._client = RESTClient(api_key=key)

    # ------------------------------------------------------------------
    # 일봉 / 기간봉 조회
    # ------------------------------------------------------------------
    def get_daily_bars(
        self,
        ticker: str,
        days: int = 200,
        end_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """최근 N일 일봉 데이터를 DataFrame으로 반환한다.

        Returns:
            DataFrame with columns: date, open, high, low, close, volume, vwap
        """
        end = end_date or date.today()
        start = end - timedelta(days=days + 30)  # 휴장일 고려 버퍼

        aggs = self._client.get_aggs(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_=start.isoformat(),
            to=end.isoformat(),
            limit=days,
            sort="asc",
        )

        rows: List[Dict[str, Any]] = []
        for bar in aggs:
            rows.append({
                "date": pd.Timestamp(bar.timestamp, unit="ms").date(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "vwap": bar.vwap,
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.tail(days).reset_index(drop=True)
        return df

    # ------------------------------------------------------------------
    # 최신 스냅샷 (현재가)
    # ------------------------------------------------------------------
    def get_snapshot(self, ticker: str) -> Dict[str, Any]:
        """종목의 최신 스냅샷(현재가, 전일 종가, 변동률 등)을 반환한다."""
        snap = self._client.get_snapshot_ticker("stocks", ticker)
        day = snap.day
        prev = snap.prev_day

        prev_close = prev.close if prev and prev.close else 0
        change_pct = ((day.close - prev_close) / prev_close * 100) if prev_close else 0

        return {
            "ticker": ticker,
            "price": day.close,
            "open": day.open,
            "high": day.high,
            "low": day.low,
            "volume": day.volume,
            "prev_close": prev_close,
            "change_pct": round(change_pct, 2),
        }

    def get_snapshots(self, tickers: List[str]) -> List[Dict[str, Any]]:
        """여러 종목의 스냅샷을 일괄 조회한다."""
        results = []
        for t in tickers:
            try:
                results.append(self.get_snapshot(t))
            except Exception as e:
                results.append({"ticker": t, "error": str(e)})
        return results

    # ------------------------------------------------------------------
    # 종목 상세 정보
    # ------------------------------------------------------------------
    def get_ticker_details(self, ticker: str) -> Dict[str, Any]:
        """종목의 기본 정보(이름, 섹터, 시가총액 등)를 반환한다."""
        detail = self._client.get_ticker_details(ticker)
        return {
            "ticker": detail.ticker,
            "name": detail.name,
            "market_cap": detail.market_cap,
            "locale": detail.locale,
            "primary_exchange": detail.primary_exchange,
            "type": detail.type,
            "currency_name": detail.currency_name,
            "description": (detail.description or "")[:500],
        }
