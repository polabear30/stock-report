"""실시간 시황 브리핑 데이터 수집 모듈

미국 증시 세션 시간, 공포탐욕지수, 실시간 지수/금리/원자재 데이터를 제공한다.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import requests
import yfinance as yf


# ---------------------------------------------------------------------------
# 시간대 정의
# ---------------------------------------------------------------------------
KST = timezone(timedelta(hours=9))
EST = timezone(timedelta(hours=-5))
EDT = timezone(timedelta(hours=-4))


def _is_dst_us() -> bool:
    """미국 서머타임(EDT) 여부를 간이 판별한다 (3월 둘째 일요일 ~ 11월 첫째 일요일)."""
    now = datetime.now(timezone.utc)
    year = now.year
    mar = datetime(year, 3, 8, tzinfo=timezone.utc)
    while mar.weekday() != 6:
        mar += timedelta(days=1)
    nov = datetime(year, 11, 1, tzinfo=timezone.utc)
    while nov.weekday() != 6:
        nov += timedelta(days=1)
    return mar <= now < nov


def get_us_timezone():
    return EDT if _is_dst_us() else EST


# ---------------------------------------------------------------------------
# 1. 미국 증시 세션 시간
# ---------------------------------------------------------------------------
def get_market_session_info() -> Dict[str, Any]:
    """미국 증시의 프리장/본장/애프터장 시간과 현재 세션 상태를 반환한다."""
    tz = get_us_timezone()
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc.astimezone(tz)
    now_kst = now_utc.astimezone(KST)

    tz_label = "EDT" if _is_dst_us() else "EST"

    sessions = {
        "프리마켓(Pre-Market)": {"start": "04:00", "end": "09:30", "start_kst": None, "end_kst": None},
        "정규장(Regular)": {"start": "09:30", "end": "16:00", "start_kst": None, "end_kst": None},
        "애프터마켓(After-Hours)": {"start": "16:00", "end": "20:00", "start_kst": None, "end_kst": None},
    }

    current_session = "휴장(Closed)"
    hour_min = now_et.hour * 60 + now_et.minute
    weekday = now_et.weekday()

    for name, info in sessions.items():
        sh, sm = map(int, info["start"].split(":"))
        eh, em = map(int, info["end"].split(":"))
        start_min = sh * 60 + sm
        end_min = eh * 60 + em

        start_dt = now_et.replace(hour=sh, minute=sm, second=0, microsecond=0)
        end_dt = now_et.replace(hour=eh, minute=em, second=0, microsecond=0)
        info["start_kst"] = start_dt.astimezone(KST).strftime("%H:%M")
        info["end_kst"] = end_dt.astimezone(KST).strftime("%H:%M")

        if weekday < 5 and start_min <= hour_min < end_min:
            current_session = name

    return {
        "현재시각_한국": now_kst.strftime("%Y-%m-%d %H:%M:%S KST"),
        "현재시각_미국": now_et.strftime("%Y-%m-%d %H:%M:%S ") + tz_label,
        "시간대": tz_label,
        "현재_세션": current_session,
        "요일": now_et.weekday(),
        "세션정보": sessions,
    }


# ---------------------------------------------------------------------------
# 2. CNN 공포탐욕지수 (fear-greed 라이브러리 사용)
# ---------------------------------------------------------------------------
_FG_LABELS = {
    "extreme fear": "극단적 공포(Extreme Fear)",
    "fear": "공포(Fear)",
    "neutral": "중립(Neutral)",
    "greed": "탐욕(Greed)",
    "extreme greed": "극단적 탐욕(Extreme Greed)",
}


def get_fear_greed_index() -> Dict[str, Any]:
    """CNN 공포탐욕지수 현재값과 히스토리를 반환한다."""
    try:
        import fear_greed

        data = fear_greed.get()
        score = data["score"]
        rating = data.get("rating", "neutral")
        history = data.get("history", {})
        indicators = data.get("indicators", {})

        label = _FG_LABELS.get(rating, rating.title())
        rating_key = rating.replace(" ", "_")

        timeline_data = []
        try:
            hist_list = fear_greed.get_history()
            seen_dates = set()
            for pt in hist_list:
                d = pt.date.strftime("%Y-%m-%d")
                if d not in seen_dates:
                    seen_dates.add(d)
                    timeline_data.append({"date": d, "score": round(pt.score, 1)})
            timeline_data.sort(key=lambda x: x["date"])
        except Exception:
            pass

        return {
            "현재점수": round(score, 1),
            "등급": label,
            "등급_원본": rating_key,
            "1주전": round(history.get("1w", 0), 1) if history.get("1w") else None,
            "1개월전": round(history.get("1m", 0), 1) if history.get("1m") else None,
            "3개월전": round(history.get("3m", 0), 1) if history.get("3m") else None,
            "6개월전": round(history.get("6m", 0), 1) if history.get("6m") else None,
            "1년전": round(history.get("1y", 0), 1) if history.get("1y") else None,
            "세부지표": {
                "시장모멘텀(S&P500)": indicators.get("market_momentum_sp500", {}),
                "주가강도(Stock Strength)": indicators.get("stock_price_strength", {}),
                "주가폭(Breadth)": indicators.get("stock_price_breadth", {}),
                "풋/콜옵션(Put/Call)": indicators.get("put_call_options", {}),
                "변동성(VIX)": indicators.get("market_volatility_vix", {}),
                "정크본드수요(Junk Bond)": indicators.get("junk_bond_demand", {}),
                "안전자산수요(Safe Haven)": indicators.get("safe_haven_demand", {}),
            },
            "타임라인": timeline_data,
            "에러": None,
        }
    except Exception as e:
        return {
            "현재점수": 50,
            "등급": "데이터 조회 실패",
            "등급_원본": "neutral",
            "1주전": None,
            "1개월전": None,
            "3개월전": None,
            "6개월전": None,
            "1년전": None,
            "세부지표": {},
            "타임라인": [],
            "에러": str(e),
        }


# ---------------------------------------------------------------------------
# 3. 실시간 시장 지수 / 금리 / 원자재
# ---------------------------------------------------------------------------
_TICKERS = {
    "나스닥(NASDAQ)": "^IXIC",
    "다우존스(Dow Jones)": "^DJI",
    "S&P 500": "^GSPC",
    "미국 10년물 국채금리": "^TNX",
    "유가 WTI": "CL=F",
    "비트코인(Bitcoin)": "BTC-USD",
    "금(Gold)": "GC=F",
    "달러인덱스(DXY)": "DX-Y.NYB",
}

_UNITS = {
    "미국 10년물 국채금리": "%",
}


def get_market_indices() -> List[Dict[str, Any]]:
    """주요 시장 지수, 금리, 원자재의 최신 시세를 반환한다."""
    results = []
    tickers_str = " ".join(_TICKERS.values())

    try:
        data = yf.download(tickers_str, period="2d", interval="1d", progress=False, threads=True)
    except Exception:
        data = None

    for name, ticker in _TICKERS.items():
        try:
            if data is not None and not data.empty:
                if len(_TICKERS) > 1:
                    close_col = data["Close"][ticker] if ticker in data["Close"].columns else None
                else:
                    close_col = data["Close"]

                if close_col is not None and len(close_col.dropna()) >= 1:
                    latest = close_col.dropna().iloc[-1]
                    prev = close_col.dropna().iloc[-2] if len(close_col.dropna()) >= 2 else latest
                    change = latest - prev
                    change_pct = (change / prev * 100) if prev != 0 else 0

                    results.append({
                        "이름": name,
                        "티커": ticker,
                        "현재가": round(float(latest), 2),
                        "전일대비": round(float(change), 2),
                        "변동률": round(float(change_pct), 2),
                        "단위": _UNITS.get(name, ""),
                        "에러": None,
                    })
                    continue

            t = yf.Ticker(ticker)
            info = t.fast_info
            price = info.get("lastPrice", 0) or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose", 0) or info.get("regularMarketPreviousClose", price)
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0

            results.append({
                "이름": name,
                "티커": ticker,
                "현재가": round(float(price), 2),
                "전일대비": round(float(change), 2),
                "변동률": round(float(change_pct), 2),
                "단위": _UNITS.get(name, ""),
                "에러": None,
            })
        except Exception as e:
            results.append({
                "이름": name,
                "티커": ticker,
                "현재가": 0,
                "전일대비": 0,
                "변동률": 0,
                "단위": _UNITS.get(name, ""),
                "에러": str(e),
            })

    return results


def get_japan_rates() -> Dict[str, Any]:
    """일본 기준금리 및 10년물 국채금리를 반환한다.

    10년물 국채금리는 일본 재무성(MOF)의 공개 CSV에서 가져온다.
    """
    jp10y_val = None
    jp10y_date = ""
    try:
        resp = requests.get(
            "https://www.mof.go.jp/jgbs/reference/interest_rate/data/jgbcm_all.csv",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.encoding = "shift_jis"
        lines = resp.text.strip().split("\n")
        for line in reversed(lines[2:]):
            cols = line.split(",")
            if len(cols) >= 11 and cols[10] and cols[10] != "-":
                jp10y_val = float(cols[10])
                jp10y_date = cols[0]
                break
    except Exception:
        pass

    return {
        "일본_기준금리": {"값": 0.50, "단위": "%", "비고": "BOJ 정책금리 (2025.03 인상, 0.50%)"},
        "일본_10년물_국채금리": {
            "값": jp10y_val,
            "단위": "%",
            "비고": f"일본 재무성(MOF) 기준일: {jp10y_date}" if jp10y_val else "데이터 조회 실패",
        },
    }


def get_options_chains(ticker: str = "QQQ", max_exp: int = 4, top_strikes: int = 22) -> Dict[str, Any]:
    """옵션 체인에서 만기별 Call/Put 미결제약정(OI) 분포와 핵심 지표를 반환한다.

    각 만기에 대해 PCR, Max Pain, Call/Put Wall, 행사가별 OI(상위 top_strikes개)를 계산한다.
    OI 미제공 시 거래량(volume)으로 대체한다. Streamlit 비의존 — 정적 HTML 내보내기에서 재사용.
    """
    MIN_ROWS = 5  # 의미 있는 차트로 인정할 최소 행사가 수

    try:
        t = yf.Ticker(ticker)
        spot = float(t.history(period="1d")["Close"].iloc[-1])
        all_exps = t.options[:20]
    except Exception as e:
        return {"티커": ticker, "현재가": None, "만기목록": [], "에러": str(e)}

    chains: List[Dict[str, Any]] = []
    for exp in all_exps:
        if len(chains) >= max_exp:
            break
        try:
            chain = t.option_chain(exp)
            calls = chain.calls[["strike", "openInterest", "volume"]].copy()
            puts = chain.puts[["strike", "openInterest", "volume"]].copy()

            calls["oi"] = calls["openInterest"].fillna(0)
            puts["oi"] = puts["openInterest"].fillna(0)
            if calls["oi"].sum() == 0 and puts["oi"].sum() == 0:
                calls["oi"] = calls["volume"].fillna(0)
                puts["oi"] = puts["volume"].fillna(0)
            if calls["oi"].sum() == 0 and puts["oi"].sum() == 0:
                continue

            lo, hi = spot * 0.85, spot * 1.15
            calls = calls[(calls["strike"] >= lo) & (calls["strike"] <= hi)]
            puts = puts[(puts["strike"] >= lo) & (puts["strike"] <= hi)]
            if calls.empty and puts.empty:
                continue

            all_strikes = sorted(set(calls["strike"]) | set(puts["strike"]))
            c_map = dict(zip(calls["strike"], calls["oi"]))
            p_map = dict(zip(puts["strike"], puts["oi"]))

            pain = {}
            for s in all_strikes:
                c_loss = sum(max(s - k, 0) * v for k, v in c_map.items())
                p_loss = sum(max(k - s, 0) * v for k, v in p_map.items())
                pain[s] = c_loss + p_loss
            max_pain = min(pain, key=pain.get) if pain else spot

            call_wall = max(c_map, key=c_map.get) if c_map else spot
            put_wall = max(p_map, key=p_map.get) if p_map else spot

            total_c = sum(c_map.values())
            total_p = sum(p_map.values())
            pcr = round(total_p / total_c, 2) if total_c > 0 else 0

            # 행사가별 OI — 상위 top_strikes개(call+put 합 기준)만, 행사가 순 정렬
            rows = [{"strike": float(s),
                     "call_oi": float(c_map.get(s, 0)),
                     "put_oi": float(p_map.get(s, 0))} for s in all_strikes]
            # OI가 0인 행사가는 제외 (빈 행 잔재 방지)
            rows = [r for r in rows if (r["call_oi"] + r["put_oi"]) > 0]
            # 데이터가 희박한 만기(행사가 수 부족)는 건너뛰고 다음 만기를 찾는다
            if len(rows) < MIN_ROWS:
                continue
            rows.sort(key=lambda r: r["call_oi"] + r["put_oi"], reverse=True)
            rows = rows[:top_strikes]
            rows.sort(key=lambda r: r["strike"], reverse=True)

            chains.append({
                "만기": exp,
                "현재가": round(spot, 2),
                "맥스페인": round(float(max_pain), 2),
                "콜월": round(float(call_wall), 2),
                "풋월": round(float(put_wall), 2),
                "PCR": pcr,
                "행사가": rows,
            })
        except Exception:
            continue

    return {"티커": ticker, "현재가": round(spot, 2), "만기목록": chains, "에러": None}


def get_put_call_ratio() -> Dict[str, Any]:
    """풋/콜 옵션 비율 지표를 반환한다.

    CBOE 직접 API가 제한되어 있어 CNN Fear & Greed의 Put/Call Options 지표를 사용한다.
    0~100 스케일이며, 낮을수록 풋 비중이 높아(공포) 높을수록 콜 비중이 높다(탐욕).
    """
    try:
        import fear_greed

        data = fear_greed.get()
        pc = data.get("indicators", {}).get("put_call_options", {})
        score = pc.get("score")
        rating = pc.get("rating", "")

        rating_map = {
            "extreme fear": "극단적 공포",
            "fear": "공포",
            "neutral": "중립",
            "greed": "탐욕",
            "extreme greed": "극단적 탐욕",
        }

        if score is not None:
            return {
                "풋콜비율": round(score, 1),
                "등급": rating_map.get(rating, rating),
                "비고": "CNN F&G Put/Call 지표 (0=극단적 공포, 100=극단적 탐욕)",
            }
    except Exception:
        pass

    return {
        "풋콜비율": None,
        "등급": "",
        "비고": "데이터 조회 실패",
    }
