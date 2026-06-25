"""기술적 분석 엔진 - 이동평균, RSI, MACD, 볼린저밴드 등"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import ta


class TechnicalAnalyzer:
    """OHLCV DataFrame을 받아 기술적 지표를 계산하고 시그널을 도출한다."""

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """주요 기술적 지표 컬럼을 추가한 DataFrame을 반환한다.

        Input columns required: close, high, low, volume
        """
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # 이동평균
        df["sma_20"] = ta.trend.sma_indicator(close, window=20)
        df["sma_50"] = ta.trend.sma_indicator(close, window=50)
        df["sma_200"] = ta.trend.sma_indicator(close, window=200)
        df["ema_20"] = ta.trend.ema_indicator(close, window=20)

        # RSI
        df["rsi_14"] = ta.momentum.rsi(close, window=14)

        # MACD
        macd = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_histogram"] = macd.macd_diff()

        # 볼린저밴드
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"] = bb.bollinger_lband()

        # 거래량 이동평균
        df["volume_sma_20"] = ta.trend.sma_indicator(volume.astype(float), window=20)

        # ADX (추세 강도)
        df["adx"] = ta.trend.adx(high, low, close, window=14)

        # Stochastic
        stoch = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
        df["stoch_k"] = stoch.stoch()
        df["stoch_d"] = stoch.stoch_signal()

        return df

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """최신 데이터 행 기준으로 매수/매도 시그널을 생성한다."""
        if df.empty or len(df) < 2:
            return {"error": "데이터 부족"}

        df = self.compute_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        signals: List[Dict[str, str]] = []

        # -- 이동평균 크로스 --
        if prev["sma_20"] <= prev["sma_50"] and latest["sma_20"] > latest["sma_50"]:
            signals.append({"type": "golden_cross", "detail": "SMA 20/50 골든크로스", "bias": "bullish"})
        if prev["sma_20"] >= prev["sma_50"] and latest["sma_20"] < latest["sma_50"]:
            signals.append({"type": "death_cross", "detail": "SMA 20/50 데드크로스", "bias": "bearish"})

        # -- 가격 vs 이동평균 위치 --
        close = latest["close"]
        if pd.notna(latest["sma_200"]):
            if close > latest["sma_200"]:
                signals.append({"type": "above_sma200", "detail": "200일선 위 (장기 상승 추세)", "bias": "bullish"})
            else:
                signals.append({"type": "below_sma200", "detail": "200일선 아래 (장기 하락 추세)", "bias": "bearish"})

        # -- RSI --
        rsi = latest["rsi_14"]
        if pd.notna(rsi):
            if rsi > 70:
                signals.append({"type": "rsi_overbought", "detail": f"RSI {rsi:.1f} — 과매수 구간", "bias": "bearish"})
            elif rsi < 30:
                signals.append({"type": "rsi_oversold", "detail": f"RSI {rsi:.1f} — 과매도 구간", "bias": "bullish"})

        # -- MACD 크로스 --
        if pd.notna(latest["macd"]) and pd.notna(latest["macd_signal"]):
            if prev["macd"] <= prev["macd_signal"] and latest["macd"] > latest["macd_signal"]:
                signals.append({"type": "macd_bullish", "detail": "MACD 상향 돌파", "bias": "bullish"})
            if prev["macd"] >= prev["macd_signal"] and latest["macd"] < latest["macd_signal"]:
                signals.append({"type": "macd_bearish", "detail": "MACD 하향 돌파", "bias": "bearish"})

        # -- 볼린저밴드 --
        if pd.notna(latest["bb_lower"]) and close <= latest["bb_lower"]:
            signals.append({"type": "bb_lower_touch", "detail": "볼린저밴드 하단 접촉", "bias": "bullish"})
        if pd.notna(latest["bb_upper"]) and close >= latest["bb_upper"]:
            signals.append({"type": "bb_upper_touch", "detail": "볼린저밴드 상단 접촉", "bias": "bearish"})

        # -- 거래량 급증 --
        if pd.notna(latest["volume_sma_20"]) and latest["volume_sma_20"] > 0:
            vol_ratio = latest["volume"] / latest["volume_sma_20"]
            if vol_ratio > 2.0:
                signals.append({"type": "volume_spike", "detail": f"거래량 급증 ({vol_ratio:.1f}x)", "bias": "neutral"})

        # 종합 판단
        bullish = sum(1 for s in signals if s["bias"] == "bullish")
        bearish = sum(1 for s in signals if s["bias"] == "bearish")

        if bullish > bearish:
            overall = "BULLISH"
        elif bearish > bullish:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        return {
            "close": round(close, 2),
            "sma_20": _r(latest.get("sma_20")),
            "sma_50": _r(latest.get("sma_50")),
            "sma_200": _r(latest.get("sma_200")),
            "rsi_14": _r(latest.get("rsi_14")),
            "macd": _r(latest.get("macd")),
            "macd_signal": _r(latest.get("macd_signal")),
            "bb_upper": _r(latest.get("bb_upper")),
            "bb_lower": _r(latest.get("bb_lower")),
            "adx": _r(latest.get("adx")),
            "signals": signals,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "overall_bias": overall,
        }


def _r(val, decimals: int = 2):
    """NaN-safe rounding helper"""
    if val is None or pd.isna(val):
        return None
    return round(float(val), decimals)
