"""거시경제 국면 분석 엔진"""

from __future__ import annotations

from typing import Any, Dict, Optional


class MacroAnalyzer:
    """거시경제 지표를 바탕으로 경제 국면을 판별하고 투자 전략을 제시한다."""

    # Kill Switch 임계값
    VIX_PANIC_THRESHOLD = 30.0
    USDKRW_RISK_THRESHOLD = 1400.0

    def classify_phase(
        self,
        t10y2y: Optional[float],
        unrate: Optional[float],
        vix: Optional[float],
        usdkrw: Optional[float],
    ) -> Dict[str, Any]:
        """경제 국면을 판별하고 전략 가이드라인을 반환한다.

        Returns:
            phase, kill_switches, strategy, reasoning 등을 포함하는 딕셔너리
        """
        kill_switches = []
        reasoning_steps = []

        # --- Kill Switch 1: VIX 패닉 ---
        if vix is not None and vix > self.VIX_PANIC_THRESHOLD:
            kill_switches.append({
                "rule": "VIX_PANIC",
                "detail": f"VIX {vix:.2f} > {self.VIX_PANIC_THRESHOLD} — 극단적 공포장",
            })

        # --- Kill Switch 2: 환율 위험 ---
        fx_risk = False
        if usdkrw is not None and usdkrw > self.USDKRW_RISK_THRESHOLD:
            fx_risk = True
            kill_switches.append({
                "rule": "FX_RISK",
                "detail": f"USD/KRW {usdkrw:.0f} > {self.USDKRW_RISK_THRESHOLD:.0f} — 환차손 위험",
            })

        # VIX 패닉이면 즉시 관망
        if any(ks["rule"] == "VIX_PANIC" for ks in kill_switches):
            reasoning_steps.append(f"VIX {vix:.2f} > 30 → 극단적 공포장 → 관망(현금)")
            return {
                "phase": "극단적 공포장",
                "kill_switches": kill_switches,
                "strategy": {"ticker": "관망(현금)", "splits": "0분할", "target_return": "0%"},
                "reasoning": reasoning_steps,
                "indicators": _indicator_dict(t10y2y, unrate, vix, usdkrw),
            }

        # --- 경제 국면 판별 ---
        phase = _base_phase(t10y2y, unrate, reasoning_steps)

        # 기본 전략 결정
        strategy = _base_strategy(phase)

        # 환율 위험 시 분할 횟수 1.5배 보수적 조정
        if fx_risk and strategy["ticker"] not in ("관망(현금)", "TMF"):
            original = strategy["splits"]
            adjusted = _multiply_splits(original, 1.5)
            reasoning_steps.append(
                f"USD/KRW {usdkrw:.0f} > 1400 → 분할 횟수 보수적 조정: {original} → {adjusted}"
            )
            strategy["splits"] = adjusted

        return {
            "phase": phase,
            "kill_switches": kill_switches,
            "strategy": strategy,
            "reasoning": reasoning_steps,
            "indicators": _indicator_dict(t10y2y, unrate, vix, usdkrw),
        }


def _base_phase(
    t10y2y: Optional[float],
    unrate: Optional[float],
    reasoning: list,
) -> str:
    if t10y2y is None or unrate is None:
        reasoning.append("데이터 부족 → 판별 불가")
        return "판별 불가"

    if t10y2y < 0:
        reasoning.append(f"T10Y2Y {t10y2y:.2f}% < 0 (장단기 금리 역전) → 수축기")
        return "수축기"

    if unrate > 4.5:
        reasoning.append(f"T10Y2Y {t10y2y:.2f}% >= 0, 실업률 {unrate:.1f}% > 4.5% → 침체기/저점")
        return "침체기/저점"

    reasoning.append(f"T10Y2Y {t10y2y:.2f}% >= 0, 실업률 {unrate:.1f}% <= 4.5% → 확장기")
    return "확장기"


def _base_strategy(phase: str) -> Dict[str, str]:
    strategies = {
        "확장기": {"ticker": "TQQQ", "splits": "40분할", "target_return": "+10%"},
        "수축기": {"ticker": "QQQ", "splits": "60분할", "target_return": "+5%"},
        "침체기/저점": {"ticker": "TMF", "splits": "40분할", "target_return": "+10%"},
    }
    return strategies.get(phase, {"ticker": "관망(현금)", "splits": "0분할", "target_return": "0%"})


def _multiply_splits(splits_str: str, factor: float) -> str:
    """'40분할' → '60분할' 식으로 분할 횟수를 factor배 조정한다."""
    try:
        num = int(splits_str.replace("분할", ""))
        adjusted = int(num * factor)
        return f"{adjusted}분할"
    except (ValueError, AttributeError):
        return splits_str


def _indicator_dict(t10y2y, unrate, vix, usdkrw) -> Dict[str, Any]:
    return {
        "t10y2y": t10y2y,
        "unrate": unrate,
        "vix": vix,
        "usdkrw": usdkrw,
    }
