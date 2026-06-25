"""FRED API를 통한 거시경제 지표 수집"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from fredapi import Fred

from config.settings import get_settings


# 조회 대상 시리즈 ID와 설명
SERIES_INFO: Dict[str, str] = {
    "T10Y2Y": "10년물-2년물 국채 금리차(%)",
    "UNRATE": "미국 실업률(%)",
    "VIXCLS": "VIX 공포지수",
    "DEXKOUS": "원/달러 환율(원)",
    "FEDFUNDS": "연방기금금리(%)",
    "CPIAUCSL": "소비자물가지수(CPI)",
}


class MacroDataClient:
    """FRED 거시경제 데이터 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or get_settings().fred_api_key
        self._fred = Fred(api_key=key)

    @staticmethod
    def _latest_value(series) -> Optional[float]:
        cleaned = series.dropna()
        return float(cleaned.iloc[-1]) if len(cleaned) > 0 else None

    def fetch_series(self, series_id: str) -> Optional[float]:
        """단일 시리즈의 최신 값을 반환한다."""
        try:
            series = self._fred.get_series(series_id)
            return self._latest_value(series)
        except Exception:
            return None

    def fetch_all_indicators(self) -> Dict[str, Any]:
        """주요 거시경제 지표를 일괄 조회하여 딕셔너리로 반환한다."""
        result: Dict[str, Any] = {}
        for sid, desc in SERIES_INFO.items():
            val = self.fetch_series(sid)
            result[sid] = {"value": val, "description": desc}
        return result

    def fetch_core_four(
        self,
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """핵심 4종 지표 (T10Y2Y, UNRATE, VIXCLS, DEXKOUS)를 튜플로 반환한다."""
        t10y2y = self.fetch_series("T10Y2Y")
        unrate = self.fetch_series("UNRATE")
        vix = self.fetch_series("VIXCLS")
        usdkrw = self.fetch_series("DEXKOUS")
        return t10y2y, unrate, vix, usdkrw
