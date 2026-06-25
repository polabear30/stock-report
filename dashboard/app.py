"""미국 주식 AI 에이전트 — 대시보드 (완전 재설계)"""

from __future__ import annotations

import sys
import os
import calendar as cal_mod
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf

# ─────────────────────────────────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="미국주식 AI 에이전트",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# 글로벌 CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css');

/* ── 폰트: * 사용 금지 (Material Icons 깨짐) → 텍스트 요소만 명시 지정 */
html, body { font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important; }
p, span, div, h1, h2, h3, h4, h5, h6,
li, td, th, label, button, input, textarea, select,
.stMarkdown, .stText, .stButton, .stRadio, .stSelectbox,
[data-testid] {
    font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;
}
/* Material Icons 예외 — 깨진 글씨 원인 */
[class*="material"], [class*="Material"],
[data-testid="stIconMaterial"], .stIconMaterial,
span[aria-hidden="true"] {
    font-family:'Material Symbols Rounded','Material Icons' !important;
}

/* ── 기본 Streamlit 헤더·메뉴 숨기기 */
header[data-testid="stHeader"]     { display:none !important; }
#MainMenu                           { display:none !important; }
.stDeployButton                     { display:none !important; }
[data-testid="stToolbar"]           { display:none !important; }
[data-testid="stDecoration"]        { display:none !important; }
[data-testid="stStatusWidget"]      { display:none !important; }

/* ── 사이드바 전체 제거 (단일 화면 운영) */
section[data-testid="stSidebar"]                 { display:none !important; }
[data-testid="stSidebarCollapsedControl"]        { display:none !important; }
[data-testid="collapsedControl"]                 { display:none !important; }

/* ── 사이드바 접기 버튼(<<) 및 상단 헤더 영역 완전 제거 */
[data-testid="stSidebarCollapseButton"]          { display:none !important; }
[data-testid="stSidebarHeader"]                  { display:none !important; min-height:0 !important; height:0 !important; padding:0 !important; }
button[data-testid="stBaseButton-headerNoPadding"] { display:none !important; }
section[data-testid="stSidebar"] > div:first-child > div:first-child { min-height:0 !important; }

/* ── 사이드바 하단 고정 버튼 영역 */
.sidebar-bottom {
    position:fixed; bottom:0; left:0;
    width:var(--sidebar-width, 240px);
    background:#111318;
    border-top:1px solid #1E2129;
    padding:12px 14px;
    z-index:999;
}

/* ── 메인 영역: 짙은 블랙 계열 */
.stApp, .stApp > div { background:#0B0D12 !important; }
.main .block-container {
    padding: 0.75rem 1.5rem 2rem !important;
    max-width: 1080px;
    margin: 0 auto !important;
    background: #0B0D12;
}

/* ── 사이드바: 딥 네이비-퍼플 그라디언트로 메인과 명확히 구분 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F0C1E 0%, #12102A 40%, #0E1628 100%) !important;
    border-right: 1px solid #2D2460 !important;
}
/* Streamlit 사이드바 내부 모든 depth 상단 여백 제거 */
section[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] > div > div > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] * { color:#A89EC4 !important; }

/* ── 라디오 기본 인디케이터(컬러 동그라미) 숨기기 */
section[data-testid="stSidebar"] .stRadio > label { display:none; }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap:2px !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    display:flex; align-items:center; gap:8px;
    padding:9px 14px; border-radius:8px; margin-bottom:2px;
    transition:background .15s; color:#9CA3AF !important;
    font-size:13px; cursor:pointer;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(167,139,250,0.1) !important;
    color: #C4B5FD !important;
}
/* 라디오 선택 인디케이터 동그라미 완전 제거 */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display:none !important; }
/* 사이드바 구분선 */
section[data-testid="stSidebar"] hr { border-color:#2D2460 !important; margin:10px 0 !important; }
/* 사이드바 버튼 */
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid #2D2460 !important;
    color: #8B7FB8 !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(167,139,250,0.12) !important;
    border-color: #A78BFA !important;
    color: #C4B5FD !important;
}
/* 전체 구분선 */
hr { border-color:#1E2129 !important; margin:12px 0 !important; }
/* tabs 기본 */
button[data-baseweb="tab"] {
    color: #4B5563 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    transition: color .15s !important;
}
div[data-testid="stTabs"] { border-bottom: 1px solid #1E2129; }

/* 탭별 개별 색상 — 나스닥/다우/S&P/10Y금리/WTI/비트코인/Gold/DXY */
button[data-baseweb="tab"]:nth-child(1) { color:#38BDF8 !important; }  /* 나스닥 — 하늘 */
button[data-baseweb="tab"]:nth-child(2) { color:#818CF8 !important; }  /* 다우존스 — 인디고 */
button[data-baseweb="tab"]:nth-child(3) { color:#34D399 !important; }  /* S&P500 — 에메랄드 */
button[data-baseweb="tab"]:nth-child(4) { color:#FB923C !important; }  /* 10Y금리 — 오렌지 */
button[data-baseweb="tab"]:nth-child(5) { color:#F87171 !important; }  /* WTI유가 — 레드 */
button[data-baseweb="tab"]:nth-child(6) { color:#FBBF24 !important; }  /* 비트코인 — 골드 */
button[data-baseweb="tab"]:nth-child(7) { color:#FCD34D !important; }  /* Gold — 옐로우 */
button[data-baseweb="tab"]:nth-child(8) { color:#A78BFA !important; }  /* DXY — 퍼플 */

/* 비선택 탭 흐리게 */
button[data-baseweb="tab"][aria-selected="false"] { opacity: 0.4 !important; }

/* 선택된 탭 — 색상 유지 + 밑줄 */
button[data-baseweb="tab"][aria-selected="true"] { opacity: 1 !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(1) { border-bottom:2px solid #38BDF8 !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(2) { border-bottom:2px solid #818CF8 !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(3) { border-bottom:2px solid #34D399 !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(4) { border-bottom:2px solid #FB923C !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(5) { border-bottom:2px solid #F87171 !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(6) { border-bottom:2px solid #FBBF24 !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(7) { border-bottom:2px solid #FCD34D !important; }
button[data-baseweb="tab"][aria-selected="true"]:nth-child(8) { border-bottom:2px solid #A78BFA !important; }
/* 캡션 */
small, [data-testid="stCaptionContainer"] p { color:#6B7280 !important; font-size:12px; }
/* info/warning */
div[data-testid="stInfo"] {
    background:#131C2B !important; border:1px solid #1D3461 !important;
    border-left:3px solid #3B82F6 !important; border-radius:8px !important;
    color:#93C5FD !important;
}
div[data-testid="stAlert"] { background:#1C1A2E !important; border-radius:8px !important; }
/* container border */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background:#111318 !important;
    border:1px solid #1E2129 !important;
    border-radius:12px !important;
}
/* 라디오/멀티셀렉트 배경 */
div[data-testid="stRadio"] label { color:#9CA3AF !important; }
div[data-testid="stMultiSelect"] * { background:#111318 !important; color:#D1D5DB !important; border-color:#1E2129 !important; }
/* 날짜 입력 */
div[data-testid="stDateInput"] * { background:#111318 !important; color:#D1D5DB !important; border-color:#1E2129 !important; }
div[data-testid="stSelectbox"] * { background:#111318 !important; color:#D1D5DB !important; border-color:#1E2129 !important; }
/* 데이터프레임 */
div[data-testid="stDataFrame"] { border:1px solid #1E2129; border-radius:10px; overflow:hidden; }
/* 메트릭 */
div[data-testid="stMetric"] {
    background:#111318 !important; border:1px solid #1E2129 !important;
    border-radius:10px !important; padding:14px !important;
}
div[data-testid="stMetricLabel"] p { color:#6B7280 !important; font-size:12px !important; }
div[data-testid="stMetricValue"] { color:#F3F4F6 !important; font-weight:700 !important; }
/* success 뱃지 */
div[data-testid="stSuccessMessage"] { background:#0F2A1E !important; border:1px solid #166534 !important; color:#4ADE80 !important; border-radius:6px !important; }
</style>""", unsafe_allow_html=True)

# JS로 사이드바 상단 여백 강제 제거
components.html("""
<script>
(function removeSidebarPadding() {
    function fix() {
        const doc = window.parent.document;

        // 1. 접기 버튼·헤더 숨기기
        ['stSidebarCollapseButton','stSidebarHeader'].forEach(id => {
            const el = doc.querySelector(`[data-testid="${id}"]`);
            if (el) { el.style.display = 'none'; el.style.height = '0'; el.style.minHeight = '0'; el.style.padding = '0'; el.style.margin = '0'; el.style.overflow = 'hidden'; }
        });
        doc.querySelectorAll('button[data-testid*="headerNoPadding"]').forEach(el => { el.style.display = 'none'; });

        // 2. 사이드바 컨텐츠 상단 여백 제거
        ['stSidebarContent','stSidebarUserContent'].forEach(id => {
            const el = doc.querySelector(`[data-testid="${id}"]`);
            if (el) { el.style.paddingTop = '0'; el.style.marginTop = '0'; }
        });

        // 3. 사이드바 내부 첫 번째 div 체인 따라가며 제거
        let el = doc.querySelector('[data-testid="stSidebar"]');
        for (let i = 0; i < 6 && el; i++) {
            el.style.paddingTop = '0';
            el.style.marginTop = '0';
            el = el.firstElementChild;
        }
    }
    fix();
    setTimeout(fix, 300);
    setTimeout(fix, 800);
    setTimeout(fix, 2000);
    new MutationObserver(fix).observe(window.parent.document.body, { childList:true, subtree:true });
})();
</script>
""", height=0)

# ─────────────────────────────────────────────────────────────────────────────
# 사이드바 제거 — 시황 브리핑 단일 화면으로 운영 (CSS로 사이드바 완전 숨김)
# ─────────────────────────────────────────────────────────────────────────────

# ═════════════════════════════════════════════════════════════════════════════
# 헬퍼 : 섹션 타이틀
# ═════════════════════════════════════════════════════════════════════════════
def section_title(num: str, ko: str, en: str = ""):
    en_part = f"<span style='font-size:12px;color:#374151;font-weight:400;margin-left:6px;'>{en}</span>" if en else ""
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin:24px 0 12px;'>"
        f"<span style='background:linear-gradient(135deg,#1D4ED8,#2563EB);"
        f"color:white;font-size:10px;font-weight:700;padding:2px 8px;"
        f"border-radius:20px;min-width:20px;text-align:center;letter-spacing:.3px;'>{num}</span>"
        f"<span style='font-size:15px;font-weight:700;"
        f"background:linear-gradient(90deg,#60A5FA,#93C5FD);"
        f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>{ko}</span>"
        f"{en_part}"
        f"</div>",
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# 시황 브리핑 페이지
# ═════════════════════════════════════════════════════════════════════════════
def render_briefing():
    from data.briefing import get_market_session_info, get_fear_greed_index, get_market_indices, get_japan_rates, get_put_call_ratio
    from data.calendar_data import get_events_next_24h, get_events_for_date, get_event_count_by_date, CATEGORY_COLORS

    session_info = get_market_session_info()

    _render_header(session_info)
    _render_session_timeline(session_info)

    # 지수 전체 너비 — 타이틀 + 인라인 새로고침 버튼 (HTML 내장)
    st.markdown(
        "<div style='display:flex;align-items:center;gap:10px;margin:24px 0 12px;'>"
        "<span style='background:linear-gradient(135deg,#1D4ED8,#2563EB);"
        "color:white;font-size:10px;font-weight:700;padding:2px 8px;"
        "border-radius:20px;min-width:20px;text-align:center;letter-spacing:.3px;'>01</span>"
        "<span style='font-size:15px;font-weight:700;"
        "background:linear-gradient(90deg,#60A5FA,#93C5FD);"
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>주요 지수 · 금리 · 원자재</span>"
        "<span style='font-size:12px;color:#374151;font-weight:400;'>Market Overview</span>"
        "<button onclick=\"window.parent.location.reload()\" title='새로고침' "
        "style='background:rgba(59,130,246,0.12);border:1px solid #3B82F6;"
        "color:#60A5FA;font-size:12px;padding:1px 8px;border-radius:5px;"
        "cursor:pointer;height:20px;line-height:1;vertical-align:middle;"
        "font-family:inherit;transition:all .15s;'>↻</button>"
        "</div>",
        unsafe_allow_html=True,
    )
    _render_indices_grid()

    # Fear & Greed + 비교지표
    section_title("02", "공포탐욕지수", "Fear & Greed Index")
    _render_fear_greed_full()

    # 풋콜비율 차트
    section_title("03", "풋/콜 비율", "Put / Call Ratio")
    _render_pcr_chart()

    # 차트
    section_title("04", "차트 분석", "Interactive Chart")
    _render_market_chart()

    # 경제 캘린더
    section_title("05", "경제 캘린더", "Economic Calendar")
    _render_economic_calendar()


# ─────────────────────────────────────────────────────────────────────────────
# 헤더 (한 줄 컴팩트)
# ─────────────────────────────────────────────────────────────────────────────
def _render_header(session: dict):
    sess = session["현재_세션"]
    is_open = "정규장" in sess
    is_pre = "프리" in sess
    sess_color = "#4ADE80" if is_open else "#FBBF24" if is_pre else "#6B7280"
    sess_bg    = "#0F2A1E" if is_open else "#2A1F0F" if is_pre else "#1A1A1A"

    html = f"""
<html><head><link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet"><style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.hdr{{
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;
  background:#111318;border:1px solid #1E2129;border-radius:14px;
  padding:16px 22px;
}}
.hdr-left h1{{
  font-size:30px;font-weight:900;margin-bottom:4px;letter-spacing:-0.5px;
  background:linear-gradient(90deg,#A78BFA,#60A5FA);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}}
.hdr-left p{{font-size:12px;color:#4B5563;}}
.hdr-right{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;}}
.chip{{
  display:flex;align-items:center;gap:6px;
  background:#1A1D24;border:1px solid #1E2129;
  border-radius:20px;padding:5px 13px;font-size:12px;color:#9CA3AF;
}}
.chip .val{{color:#D1D5DB;font-weight:600;}}
.sess-chip{{
  display:flex;align-items:center;gap:6px;
  background:{sess_bg};border:1px solid {sess_color}44;
  border-radius:20px;padding:5px 14px;font-size:12px;
  color:{sess_color};font-weight:600;
}}
.dot{{width:7px;height:7px;border-radius:50%;background:{sess_color};
      box-shadow:0 0 6px {sess_color};}}
</style></head><body>
<div class="hdr">
  <div class="hdr-left">
    <h1>실시간 시황 브리핑</h1>
    <p>미국 증시 종합 현황 — 지수 · 금리 · 원자재 · 경제 캘린더</p>
  </div>
  <div class="hdr-right">
    <div class="chip">🇰🇷 KST &nbsp;<span class="val">{session['현재시각_한국']}</span></div>
    <div class="chip">🇺🇸 EDT &nbsp;<span class="val">{session['현재시각_미국']}</span></div>
    <div class="sess-chip"><span class="dot"></span>{sess}</div>
  </div>
</div>
</body></html>"""
    components.html(html, height=100)


# ─────────────────────────────────────────────────────────────────────────────
# 세션 타임라인 (시각적 바)
# ─────────────────────────────────────────────────────────────────────────────
def _render_session_timeline(session: dict):
    tz = session["시간대"]
    is_dst = (tz == "EDT")
    dst_label = "☀️ EDT, UTC−4" if is_dst else "❄️ EST, UTC−5"
    current = session["현재_세션"]
    info = session["세션정보"]

    chips = ""
    for name, times in info.items():
        is_active = (name == current)
        if "프리" in name:
            icon, color = "🌅", "#FBBF24"
        elif "정규" in name:
            icon, color = "📈", "#4ADE80"
        else:
            icon, color = "🌙", "#818CF8"

        if is_active:
            style = f"background:{color}18;border:1px solid {color}55;"
            name_color = "#F3F4F6"
            dot = f'<span style="width:6px;height:6px;border-radius:50%;background:{color};box-shadow:0 0 5px {color};display:inline-block;margin-right:5px;"></span>'
        else:
            style = "background:#111318;border:1px solid #1E2129;"
            name_color = "#6B7280"
            dot = ""

        chips += f"""
<div style="{style}border-radius:8px;padding:7px 13px;display:flex;align-items:center;gap:8px;white-space:nowrap;">
  <span style="font-size:14px;">{icon}</span>
  <div>
    <div style="font-size:12px;font-weight:600;color:{name_color};">{dot}{name}</div>
    <div style="font-size:10px;color:#4B5563;margin-top:1px;">
      🇺🇸 {times['start']}–{times['end']} &nbsp;🇰🇷 {times['start_kst']}–{times['end_kst']}
    </div>
  </div>
</div>"""

    dst_color = "#FBBF24" if is_dst else "#60A5FA"
    dst_bg    = "#2A1F0F" if is_dst else "#0F1C2E"
    dst_chip  = (
        f'<div style="background:{dst_bg};border:1px solid {dst_color}44;border-radius:8px;'
        f'padding:7px 13px;display:flex;align-items:center;gap:6px;white-space:nowrap;">'
        f'<span style="font-size:13px;">{"☀️" if is_dst else "❄️"}</span>'
        f'<div>'
        f'<div style="font-size:12px;font-weight:600;color:{dst_color};">{"써머타임 적용중" if is_dst else "표준시 적용중"}</div>'
        f'<div style="font-size:10px;color:#4B5563;margin-top:1px;">{"EDT, UTC−4" if is_dst else "EST, UTC−5"}</div>'
        f'</div></div>'
    )

    html = f"""
<html><head><link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet"><style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.row{{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}}
</style></head><body>
<div class="row">
  {dst_chip}
  <span style="color:#1E2129;font-size:16px;">|</span>
  {chips}
</div>
</body></html>"""
    components.html(html, height=58)


# ─────────────────────────────────────────────────────────────────────────────
# 01. 지수 그리드 (custom HTML cards)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _fetch_indices_data(v: int = 1):
    from data.briefing import get_market_indices, get_japan_rates, get_put_call_ratio
    return get_market_indices(), get_japan_rates(), get_put_call_ratio()


# 지수 이름 → yfinance 티커 매핑 (get_market_indices() 반환 순서와 동일)
_IDX_TICKER_MAP = [
    "^IXIC", "^DJI", "^GSPC", "^TNX",
    "CL=F", "BTC-USD", "GC=F", "DX-Y.NYB",
]


@st.cache_data(ttl=60)
def _fetch_mini_candles(_key: int = 0):
    """각 지수의 오늘 일봉 캔들 (1분봉 집계 → 오늘 OHLC)"""
    result = {}
    for ticker in _IDX_TICKER_MAP:
        try:
            t = yf.Ticker(ticker)
            # 오늘 1분봉으로 당일 캔들 집계
            df = t.history(period="1d", interval="1m")
            if not df.empty:
                result[ticker] = {
                    "O": float(df["Open"].iloc[0]),
                    "H": float(df["High"].max()),
                    "L": float(df["Low"].min()),
                    "C": float(df["Close"].iloc[-1]),
                    "live": True,
                }
            else:
                # 장 마감 후 — 일봉 마지막 캔들
                df2 = t.history(period="5d", interval="1d")
                df2 = df2[df2["Close"] > 0]
                if not df2.empty:
                    r = df2.iloc[-1]
                    result[ticker] = {
                        "O": float(r["Open"]), "H": float(r["High"]),
                        "L": float(r["Low"]),  "C": float(r["Close"]),
                        "live": False,
                    }
        except Exception:
            pass
    return result


def _svg_candle(O: float, H: float, L: float, C: float,
                w: int = 54, h: int = 38) -> str:
    """SVG 미니 캔들 생성"""
    is_bull = C >= O
    color = "#4ADE80" if is_bull else "#F87171"
    pad = 3
    price_range = H - L or H * 0.01 or 1

    def py(p):
        return pad + (H - p) / price_range * (h - pad * 2)

    y_h, y_l = py(H), py(L)
    y_o, y_c = py(O), py(C)
    cx = w / 2
    bw = w * 0.38
    bt = min(y_o, y_c)
    bh = max(abs(y_c - y_o), 2)

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
        f'<line x1="{cx:.1f}" y1="{y_h:.1f}" x2="{cx:.1f}" y2="{y_l:.1f}" '
        f'stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>'
        f'<rect x="{cx - bw/2:.1f}" y="{bt:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
        f'fill="{color}" rx="2"/>'
        f'</svg>'
    )


def _render_indices_grid():
    indices, japan, pcr = _fetch_indices_data()
    candles = _fetch_mini_candles(_key=st.session_state.get("idx_refresh_key", 0))

    # 지수 8개 + 캔들 매핑
    items = []
    for i, item in enumerate(indices):
        ticker = _IDX_TICKER_MAP[i] if i < len(_IDX_TICKER_MAP) else None
        candle = candles.get(ticker)
        svg = _svg_candle(candle["O"], candle["H"], candle["L"], candle["C"]) if candle else ""
        live_dot = ('<span style="display:inline-block;width:5px;height:5px;border-radius:50%;'
                    'background:#4ADE80;box-shadow:0 0 4px #4ADE80;margin-left:4px;vertical-align:middle;"></span>'
                    if candle and candle.get("live") else "")
        items.append({
            "name": item["이름"], "live_dot": live_dot,
            "price": f"{item['현재가']:,.2f}{item['단위']}",
            "change": item["변동률"],
            "inverse": "금리" in item["이름"],
            "svg": svg,
        })

    pcr_val = pcr.get("풋콜비율") if isinstance(pcr, dict) else None
    pcr_label = pcr.get("등급", "") if isinstance(pcr, dict) else ""
    items.append({"name": "풋/콜 지표 📊", "live_dot": "", "price": str(pcr_val) if pcr_val else "—", "change": None, "label": pcr_label, "inverse": False, "svg": ""})

    cards_html = ""
    for item in items:
        change = item.get("change")
        inv = item.get("inverse", False)
        svg = item.get("svg", "")

        if change is None:
            chg_html = f'<div style="font-size:11px;color:#4B5563;margin-top:4px;">{item.get("label","")}</div>'
        else:
            positive = (change > 0 and not inv) or (change < 0 and inv)
            color = "#4ADE80" if positive else "#F87171" if change != 0 else "#6B7280"
            arrow = "▲" if change > 0 else "▼" if change < 0 else "—"
            chg_html = f'<div style="font-size:12px;color:{color};font-weight:600;margin-top:4px;">{arrow} {abs(change):.2f}%</div>'

        cards_html += f"""
<div style="background:#111318;border:1px solid #1E2129;border-radius:12px;
     padding:14px 16px;display:flex;align-items:center;justify-content:space-between;min-width:0;gap:8px;">
  <div style="flex:1;min-width:0;">
    <div style="font-size:11px;color:#6B7280;font-weight:500;margin-bottom:5px;
         white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
      {item['name']}{item.get('live_dot','')}
    </div>
    <div style="font-size:18px;font-weight:800;color:#F3F4F6;letter-spacing:-0.5px;line-height:1.1;">{item['price']}</div>
    {chg_html}
  </div>
  <div style="flex-shrink:0;">{svg}</div>
</div>"""

    html = f"""
<html><head><link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet"><style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;}}
</style></head><body>
<div class="grid">{cards_html}</div>
</body></html>"""
    components.html(html, height=355)


# ─────────────────────────────────────────────────────────────────────────────
# 02. 공포탐욕지수 (가로 레이아웃)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _fetch_fear_greed(v: int = 3):
    from data.briefing import get_fear_greed_index
    return get_fear_greed_index()


def _render_fear_greed_full():
    fg = _fetch_fear_greed()
    score = fg["현재점수"]
    label = fg["등급"]
    rating = fg["등급_원본"]

    # 색상
    color_map = {
        "extreme_fear": "#EF4444", "fear": "#F97316", "neutral": "#EAB308",
        "greed": "#22C55E", "extreme_greed": "#16A34A",
    }
    gauge_color = color_map.get(rating, "#6B7280")

    col_gauge, col_detail = st.columns([1, 2])

    with col_gauge:
        # 게이지
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=score,
            number={"font": {"size": 52, "color": gauge_color}, "suffix": ""},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {
                    "range": [0, 100], "tickwidth": 1, "tickcolor": "#374151",
                    "tickvals": [0, 25, 50, 75, 100],
                    "ticktext": ["극공포", "공포", "중립", "탐욕", "극탐욕"],
                    "tickfont": {"size": 9, "color": "#6B7280"},
                },
                "bar": {"color": gauge_color, "thickness": 0.28},
                "bgcolor": "#111318", "borderwidth": 0,
                "steps": [
                    {"range": [0, 25],  "color": "#1F0F0F"},
                    {"range": [25, 45], "color": "#1F160A"},
                    {"range": [45, 55], "color": "#1A1A0A"},
                    {"range": [55, 75], "color": "#0A1F12"},
                    {"range": [75, 100],"color": "#071A0D"},
                ],
            },
        ))
        fig.update_layout(
            height=260, margin=dict(t=20, b=0, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#9CA3AF"),
        )
        st.plotly_chart(fig, key="fg_gauge", use_container_width=True, config={"displayModeBar": False})

        # 등급 뱃지
        st.markdown(
            f"<div style='text-align:center;margin-top:-10px;'>"
            f"<span style='background:{gauge_color}22;color:{gauge_color};"
            f"border:1px solid {gauge_color}55;border-radius:20px;"
            f"padding:4px 16px;font-size:14px;font-weight:700;'>{label}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_detail:
        # 기간 비교 카드
        compare_data = [
            ("현재", score, None),
            ("1주 전", fg.get("1주전"), score - (fg.get("1주전") or score)),
            ("1개월 전", fg.get("1개월전"), score - (fg.get("1개월전") or score)),
            ("3개월 전", fg.get("3개월전"), score - (fg.get("3개월전") or score)),
            ("6개월 전", fg.get("6개월전"), score - (fg.get("6개월전") or score)),
            ("1년 전", fg.get("1년전"), score - (fg.get("1년전") or score)),
        ]

        cards = ""
        for lbl, val, diff in compare_data:
            if val is None:
                continue
            diff_html = ""
            if diff is not None:
                dc = "#4ADE80" if diff > 0 else "#F87171" if diff < 0 else "#6B7280"
                diff_html = f"<div style='font-size:11px;color:{dc};margin-top:2px;'>{diff:+.0f}</div>"
            highlight = "border:1px solid #A78BFA44;background:#1A1830;" if lbl == "현재" else "border:1px solid #1E2129;background:#111318;"
            cards += f"""
<div style="{highlight}border-radius:10px;padding:12px 14px;text-align:center;">
  <div style="font-size:11px;color:#6B7280;margin-bottom:4px;">{lbl}</div>
  <div style="font-size:22px;font-weight:800;color:#F3F4F6;">{int(val)}</div>
  {diff_html}
</div>"""

        components.html(f"""
<html><head><link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet"><style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px;}}
</style></head><body>
<div class="grid">{cards}</div>
</body></html>""", height=110)

        # 세부 지표
        indicators = fg.get("세부지표", {})
        if indicators:
            ind_color = {
                "extreme fear": "#EF4444", "fear": "#F97316", "neutral": "#EAB308",
                "greed": "#22C55E", "extreme greed": "#16A34A",
            }
            rows_html = ""
            for name, info in indicators.items():
                if isinstance(info, dict) and "score" in info:
                    s = round(info["score"], 1)
                    r = info.get("rating", "")
                    c = ind_color.get(r, "#6B7280")
                    pct = int(s)
                    rows_html += f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:7px;">
  <div style="font-size:12px;color:#9CA3AF;min-width:160px;">{name}</div>
  <div style="flex:1;background:#1A1D24;border-radius:4px;height:6px;overflow:hidden;">
    <div style="width:{pct}%;height:6px;background:{c};border-radius:4px;"></div>
  </div>
  <div style="font-size:12px;color:{c};font-weight:600;min-width:30px;text-align:right;">{s}</div>
</div>"""

            components.html(f"""
<html><head><link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet"><style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
</style></head><body>
<div style="font-size:11px;color:#4B5563;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;">세부 지표</div>
{rows_html}
</body></html>""", height=len(indicators) * 30 + 30)

    # 타임라인 차트 (전체 너비)
    timeline = fg.get("타임라인", [])
    if timeline:
        tdf = pd.DataFrame(timeline)
        tdf["date"] = pd.to_datetime(tdf["date"])

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=tdf["date"], y=tdf["score"],
            mode="lines", name="공포탐욕",
            line=dict(color="#A78BFA", width=2),
            fill="tozeroy",
            fillcolor="rgba(167,139,250,0.08)",
        ))

        # 과거 시점 마커 표시
        today = tdf["date"].max()
        marker_defs = [
            ("현재", 0, "#A78BFA"),
            ("1주 전", 7, "#60A5FA"),
            ("1개월 전", 30, "#34D399"),
            ("3개월 전", 90, "#FB923C"),
            ("6개월 전", 180, "#F87171"),
            ("1년 전", 365, "#EF4444"),
        ]
        marker_x, marker_y, marker_text, marker_colors = [], [], [], []
        for lbl, days_ago, color in marker_defs:
            target = today - timedelta(days=days_ago)
            closest = tdf.iloc[(tdf["date"] - target).abs().argsort()[:1]]
            if not closest.empty:
                row = closest.iloc[0]
                marker_x.append(row["date"])
                marker_y.append(row["score"])
                marker_text.append(f"{lbl}<br>{row['score']:.1f}점")
                marker_colors.append(color)

        if marker_x:
            fig2.add_trace(go.Scatter(
                x=marker_x, y=marker_y,
                mode="markers+text",
                marker=dict(size=10, color=marker_colors, line=dict(width=2, color="#0B0D12")),
                text=[f"{s:.0f}" for s in marker_y],
                textposition="top center",
                textfont=dict(size=10, color="#E5E7EB"),
                hovertext=marker_text,
                hoverinfo="text",
                name="시점별 점수",
                showlegend=False,
            ))

        fig2.add_hline(y=25, line_dash="dot", line_color="#EF4444", line_width=1, opacity=0.5,
                       annotation_text="공포", annotation_font_color="#EF4444",
                       annotation_font_size=9, annotation_position="left")
        fig2.add_hline(y=50, line_dash="dot", line_color="#6B7280", line_width=1, opacity=0.3,
                       annotation_text="중립", annotation_font_color="#6B7280",
                       annotation_font_size=9, annotation_position="left")
        fig2.add_hline(y=75, line_dash="dot", line_color="#22C55E", line_width=1, opacity=0.5,
                       annotation_text="탐욕", annotation_font_color="#22C55E",
                       annotation_font_size=9, annotation_position="left")
        fig2.update_layout(
            height=260, margin=dict(t=20, b=30, l=50, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#111318",
            font=dict(color="#6B7280", size=11),
            xaxis=dict(gridcolor="#1E2129", color="#6B7280"),
            yaxis=dict(range=[0, 100], gridcolor="#1E2129", color="#6B7280"),
            showlegend=False, hovermode="x unified",
        )
        st.plotly_chart(fig2, key="fg_timeline", use_container_width=True, config={"displayModeBar": False})
        st.caption(f"최근 {len(timeline)}일 데이터 · 현재 {score}점 ({label})")


# ─────────────────────────────────────────────────────────────────────────────
# 03. 풋/콜 비율 차트
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner="옵션 체인 로딩중…")
def _fetch_options_chain(ticker: str = "QQQ"):
    MIN_ROWS = 5  # 의미 있는 차트로 인정할 최소 행사가 수
    t = yf.Ticker(ticker)
    spot = float(t.history(period="1d")["Close"].iloc[-1])
    all_exps = t.options[:20]
    result = []
    for exp in all_exps:
        if len(result) >= 4:
            break
        try:
            chain = t.option_chain(exp)
            calls = chain.calls[["strike", "openInterest", "volume"]].copy()
            puts  = chain.puts [["strike", "openInterest", "volume"]].copy()

            # yfinance OI가 0인 경우 volume으로 대체
            calls["oi"] = calls["openInterest"].fillna(0)
            puts["oi"]  = puts["openInterest"].fillna(0)
            if calls["oi"].sum() == 0 and puts["oi"].sum() == 0:
                calls["oi"] = calls["volume"].fillna(0)
                puts["oi"]  = puts["volume"].fillna(0)

            # volume도 0이면 스킵
            if calls["oi"].sum() == 0 and puts["oi"].sum() == 0:
                continue

            # 현재가 ±15% 범위만
            lo, hi = spot * 0.85, spot * 1.15
            calls = calls[(calls["strike"] >= lo) & (calls["strike"] <= hi)]
            puts  = puts [(puts ["strike"] >= lo) & (puts ["strike"] <= hi)]

            # OI 0인 행사가 제외
            calls = calls[calls["oi"] > 0]
            puts  = puts [puts ["oi"] > 0]

            # 데이터 희박 만기(콜·풋 한쪽이 비거나 행사가 수 부족) 건너뛰고 다음 만기 탐색
            nonzero = len(set(calls["strike"]) | set(puts["strike"]))
            if nonzero < MIN_ROWS or calls["oi"].sum() == 0 or puts["oi"].sum() == 0:
                continue

            # Max Pain
            all_strikes = sorted(set(calls["strike"]) | set(puts["strike"]))
            pain = {}
            for s in all_strikes:
                c_loss = sum(max(s - k, 0) * v for k, v in zip(calls["strike"], calls["oi"]))
                p_loss = sum(max(k - s, 0) * v for k, v in zip(puts["strike"],  puts["oi"]))
                pain[s] = c_loss + p_loss
            max_pain = min(pain, key=pain.get) if pain else spot

            # Call/Put Wall
            call_wall = calls.loc[calls["oi"].idxmax(), "strike"] if not calls.empty else spot
            put_wall  = puts.loc [puts ["oi"].idxmax(), "strike"] if not puts.empty else spot

            # PCR (volume 기반)
            total_c = calls["oi"].sum()
            total_p = puts["oi"].sum()
            pcr = round(total_p / total_c, 2) if total_c > 0 else 0

            result.append({"exp": exp, "calls": calls, "puts": puts,
                           "spot": spot, "max_pain": max_pain,
                           "call_wall": call_wall, "put_wall": put_wall, "pcr": pcr})
        except Exception:
            continue
    return result, ticker


def _make_oi_chart(data: dict, title: str) -> go.Figure:
    calls = data["calls"]
    puts  = data["puts"]
    spot  = data["spot"]
    max_pain  = data["max_pain"]
    call_wall = data["call_wall"]
    put_wall  = data["put_wall"]
    pcr       = data["pcr"]

    fig = go.Figure()

    # Call — 초록 양수
    fig.add_trace(go.Bar(
        y=calls["strike"], x=calls["oi"],
        orientation="h", name="Call",
        marker_color="rgba(74,222,128,0.75)",
        hovertemplate="Strike %{y}<br>Call %{x:,}<extra></extra>",
    ))
    # Put — 빨강 음수
    fig.add_trace(go.Bar(
        y=puts["strike"], x=-puts["oi"],
        orientation="h", name="Put",
        marker_color="rgba(248,113,113,0.75)",
        hovertemplate="Strike %{y}<br>Put %{x:,}<extra></extra>",
    ))

    # 기준선들
    def hline(y, color, dash, label):
        fig.add_hline(y=y, line_color=color, line_dash=dash, line_width=1.2,
                      annotation_text=f" {label} {y:,.0f}",
                      annotation_font_color=color, annotation_font_size=9,
                      annotation_position="right")

    hline(spot,      "#FFFFFF", "solid", "Spot")
    hline(max_pain,  "#FBBF24", "dot",   "Max Pain")
    hline(call_wall, "#4ADE80", "dash",  "Call Wall")
    hline(put_wall,  "#F87171", "dash",  "Put Wall")

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>  <span style='font-size:11px;color:#6B7280;'>Exp {data['exp']}  |  PCR {pcr}</span>",
                   font=dict(size=13, color="#C8D6F8"), x=0),
        height=420,
        barmode="overlay",
        margin=dict(t=36, b=30, l=10, r=120),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#111318",
        font=dict(color="#6B7280", size=10, family="Pretendard"),
        showlegend=False,
        xaxis=dict(gridcolor="#1E2129", color="#6B7280", zeroline=True,
                   zerolinecolor="#374151", zerolinewidth=1, title="Open Interest"),
        yaxis=dict(gridcolor="#1E2129", color="#6B7280", title="Strike Price"),
        hovermode="y unified",
    )
    return fig


def _render_pcr_chart():
    ticker_choice = "QQQ"
    st.caption(f"📌 {ticker_choice} 옵션 체인 — 행사가별 Call/Put Volume (OI 미제공 시 Volume 대체) · 현재가 기준 ±15%")

    chain_list, used_ticker = _fetch_options_chain(ticker_choice)

    if not chain_list:
        st.warning(f"{used_ticker} 옵션 데이터를 불러올 수 없습니다.")
        return

    titles = ["1차 만기 (Nearest)", "2차 만기", "3차 만기", "4차 만기"]
    show = chain_list[:4]

    # 2열 2행 그리드
    for row in range(0, len(show), 2):
        cols = st.columns(2)
        for col_i, data in enumerate(show[row:row+2]):
            with cols[col_i]:
                fig = _make_oi_chart(data, titles[row + col_i])
                st.plotly_chart(fig, use_container_width=True,
                                config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# 04. 차트 분석
# ─────────────────────────────────────────────────────────────────────────────
_CHART_ITEMS = [
    ("나스닥", "^IXIC"), ("다우존스", "^DJI"), ("S&P500", "^GSPC"),
    ("10Y금리", "^TNX"), ("WTI유가", "CL=F"), ("비트코인", "BTC-USD"),
    ("Gold", "GC=F"), ("DXY", "DX-Y.NYB"),
]
_TF_MAP = {
    "일봉":   {"interval": "1d",  "resample": None,   "period": "10y"},
    "주봉":   {"interval": "1wk", "resample": None,   "period": "10y"},
    "월봉":   {"interval": "1mo", "resample": None,   "period": "max"},
}
_MA_COLORS = {5: "#F87171", 10: "#FB923C", 20: "#FBBF24", 100: "#34D399", 200: "#818CF8", 400: "#F472B6"}
_MA_LABELS = {5: "5일선", 10: "10일선", 20: "20일선", 100: "100일선", 200: "200일선", 400: "400일선"}


@st.cache_data(ttl=120, show_spinner="차트 데이터 로딩중…")
def _load_chart(ticker: str, interval: str, period: str, _v: int = 2) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    if df.empty:
        return df
    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[cols]

    # ① Close=0 또는 NaN 제거 (공통)
    df = df[df["Close"] > 0].dropna(subset=["Close"])

    is_crypto   = ticker.endswith("-USD")
    is_daily_up = interval in ("1d", "1wk", "1mo")

    # ② 일봉↑: Volume=0인 휴장일 제거 (인트라데이 09:30봉은 Volume=0이라 제외)
    if not is_crypto and is_daily_up and "Volume" in df.columns:
        df = df[df["Volume"] > 0]

    # ③ 인트라데이: 주말 인덱스 제거 (yfinance가 간혹 포함)
    if not is_crypto and not is_daily_up:
        df.index = pd.to_datetime(df.index)
        df = df[df.index.dayofweek < 5]   # 0=월 … 4=금

    return df


def _render_market_chart():
    # 컨트롤 박스 스타일
    st.markdown("""<style>
/* 차트 컨트롤 박스 */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stRadio"]) {
    background: #161B2E;
    border: 1px solid #2D3561;
    border-radius: 12px;
    padding: 10px 18px;
    align-items: center;
    margin-bottom: 12px;
}
/* 봉 기준 — 모든 텍스트 강제 표시 */
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] label span,
div[data-testid="stRadio"] label div,
div[data-testid="stRadio"] div[role="radiogroup"] p,
div[data-testid="stRadio"] div[role="radiogroup"] span {
    color: #C8D6F8 !important;
    font-size: 13px !important;
    opacity: 1 !important;
    visibility: visible !important;
}
div[data-testid="stRadio"] label:has(input:checked),
div[data-testid="stRadio"] label:has(input:checked) span,
div[data-testid="stRadio"] label:has(input:checked) p {
    color: #D8B4FE !important;
    font-weight: 700 !important;
}
/* 이동평균선 체크박스 */
div[data-testid="stCheckbox"] {
    white-space: nowrap !important;
}
div[data-testid="stCheckbox"] label p,
div[data-testid="stCheckbox"] label span {
    color: #C8D6F8 !important;
    font-size: 12px !important;
    white-space: nowrap !important;
}
div[data-testid="stCheckbox"] input[type="checkbox"] { accent-color: #A78BFA; }
</style>""", unsafe_allow_html=True)

    ctrl_col, ma_col = st.columns([4, 3])
    with ctrl_col:
        tf_key = st.radio(
            "봉 기준", list(_TF_MAP.keys()),
            horizontal=True, index=0, key="chart_tf",
        )
    # 이동평균선 체크박스 — 봉기준과 같은 행, 한 줄 인라인
    ma_list = []
    defaults = {5: True, 10: False, 20: True, 100: False, 200: False, 400: False}
    with ma_col:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#6B7DB3;letter-spacing:0.5px;text-transform:uppercase;margin-bottom:4px;'>이동평균선</div>", unsafe_allow_html=True)
        # 6개를 한 줄에
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        for col, ma in zip([c1,c2,c3,c4,c5,c6], [5,10,20,100,200,400]):
            with col:
                if st.checkbox(f"{ma}", value=defaults[ma], key=f"ma_{ma}"):
                    ma_list.append(ma)

    tf = _TF_MAP[tf_key]
    tabs = st.tabs([name for name, _ in _CHART_ITEMS])
    for idx, (name, ticker) in enumerate(_CHART_ITEMS):
        with tabs[idx]:
            _draw_single_chart(name, ticker, tf, tf_key, ma_list)


def _draw_single_chart(name, ticker, tf, tf_key, ma_list):
    try:
        raw = _load_chart(ticker, tf["interval"], tf["period"])
        if raw.empty:
            st.warning(f"{name}: 데이터 없음")
            return
        df = raw.copy()
        if tf["resample"]:
            df = df.resample(tf["resample"]).agg(
                {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
            ).dropna()
            df = df[df["Close"] > 0]
            if not ticker.endswith("-USD") and "Volume" in df.columns:
                df = df[df["Volume"] > 0]

        # ── x축: string category 방식 (일/주/월봉은 데이터량 적어 안전)
        df.index = pd.to_datetime(df.index)
        x_labels = df.index.strftime("%Y-%m-%d").tolist()
        n = len(x_labels)

        for ma in ma_list:
            df[f"MA{ma}"] = df["Close"].rolling(ma).mean()

        has_vol = "Volume" in df.columns and df["Volume"].sum() > 0
        fig = make_subplots(
            rows=2 if has_vol else 1, cols=1, shared_xaxes=True,
            vertical_spacing=0.03, row_heights=[0.75, 0.25] if has_vol else [1],
        )

        fig.add_trace(go.Candlestick(
            x=x_labels,
            open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name=name,
            increasing_line_color="#4ADE80", increasing_fillcolor="#4ADE80",
            decreasing_line_color="#F87171", decreasing_fillcolor="#F87171",
        ), row=1, col=1)

        for ma in ma_list:
            col_n = f"MA{ma}"
            if col_n in df.columns:
                valid_mask = df[col_n].notna()
                if valid_mask.any():
                    s_x = [x_labels[i] for i, v in enumerate(valid_mask) if v]
                    s_y = df[col_n].dropna().values.tolist()
                    fig.add_trace(go.Scatter(
                        x=s_x, y=s_y, mode="lines", name=f"MA{ma}",
                        line=dict(width=1.5, color=_MA_COLORS.get(ma, "#6B7280")),
                    ), row=1, col=1)

        if has_vol:
            colors = ["#4ADE80" if c >= o else "#F87171"
                      for c, o in zip(df["Close"], df["Open"])]
            fig.add_trace(go.Bar(
                x=x_labels, y=df["Volume"], name="거래량",
                marker_color=colors, opacity=0.4, showlegend=False,
            ), row=2, col=1)

        G = "#1E2129"
        nticks = min(12, max(6, n // 30))

        # 초기 뷰: 최근 120봉의 y범위를 직접 계산해 지정
        view_df = df.iloc[max(0, n - 120):]
        y_lo = float(view_df["Low"].min())  * 0.995
        y_hi = float(view_df["High"].max()) * 1.005

        x_axis_common = dict(
            gridcolor=G, color="#6B7280", type="category",
            nticks=nticks, tickangle=-30,
            range=[max(0, n - 120) - 0.5, n - 0.5],
        )

        fig.update_layout(
            height=580, margin=dict(t=20, b=20, l=20, r=60),
            paper_bgcolor="#0D1117", plot_bgcolor="#111318",
            font=dict(color="#6B7280", size=11),
            legend=dict(orientation="h", y=1.02, x=0,
                        font=dict(size=11, color="#C8D6F8"), bgcolor="rgba(0,0,0,0)"),
            xaxis_rangeslider_visible=False,
            yaxis=dict(title="", gridcolor=G, color="#6B7280", side="right",
                       showgrid=True, range=[y_lo, y_hi]),
            xaxis=dict(**x_axis_common),
            hovermode="x unified", dragmode="zoom",
        )
        if has_vol:
            fig.update_layout(
                xaxis2=dict(**x_axis_common,
                            rangeslider=dict(visible=True, thickness=0.04)),
                yaxis2=dict(gridcolor=G, color="#6B7280", side="right"),
            )
        else:
            fig.update_layout(
                xaxis=dict(**x_axis_common,
                           rangeslider=dict(visible=True, thickness=0.05)),
            )

        st.plotly_chart(fig, key=f"ch_{ticker}_{tf_key}", use_container_width=True,
                        config={"scrollZoom": True, "displayModeBar": True,
                                "modeBarButtonsToRemove": ["autoScale2d", "lasso2d", "select2d"]})

        last_c = float(df["Close"].iloc[-1])
        first_c = float(df["Close"].iloc[0])
        pct = (last_c - first_c) / first_c * 100 if first_c else 0
        color = "#4ADE80" if pct >= 0 else "#F87171"
        st.markdown(
            f"<div style='display:flex;gap:20px;font-size:12px;color:#6B7280;margin-top:4px;'>"
            f"<span>기간 수익률 <b style='color:{color}'>{pct:+.2f}%</b></span>"
            f"<span>최고 <b style='color:#F3F4F6'>{float(df['High'].max()):,.2f}</b></span>"
            f"<span>최저 <b style='color:#F3F4F6'>{float(df['Low'].min()):,.2f}</b></span>"
            f"<span>봉 수 <b style='color:#F3F4F6'>{len(df)}</b></span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"차트 로딩 실패: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# 04. 경제 캘린더
# ─────────────────────────────────────────────────────────────────────────────
_TAG_COLORS = {
    "FOMC": "#60A5FA", "FOMC 인사발언": "#A78BFA", "고용지표": "#FB923C",
    "물가지표": "#F87171", "경기지표": "#4ADE80", "주택지표": "#FBBF24",
    "소비/심리": "#60A5FA", "국채경매": "#9CA3AF", "옵션만기": "#6B7280",
    "일본(BOJ)": "#F87171", "백악관/행정부": "#A78BFA",
}
_TAG_ICONS = {
    "FOMC": "🔵", "FOMC 인사발언": "🟣", "고용지표": "🟠", "물가지표": "🔴",
    "경기지표": "🟢", "주택지표": "🟡", "소비/심리": "🔵", "국채경매": "⚪",
    "옵션만기": "⚫", "일본(BOJ)": "🔴", "백악관/행정부": "🟣",
}


def _render_economic_calendar():
    from data.calendar_data import get_events_next_24h, get_events_for_date, get_event_count_by_date, CATEGORY_COLORS

    # ── 향후 24시간 ──────────────────────────────────────────
    next_events = get_events_next_24h()

    if next_events:
        st.markdown(
            "<div style='font-size:13px;font-weight:600;color:#9CA3AF;"
            "margin-bottom:10px;'>⏰ 향후 24시간 주요 일정</div>",
            unsafe_allow_html=True,
        )
        items_html = ""
        for ev in sorted(next_events, key=lambda x: x["시간_KST"]):
            cat = ev["카테고리"]
            color = _TAG_COLORS.get(cat, "#6B7280")
            speaker = f" · {ev['인사정보']}" if ev.get("인사정보") else ""
            details = []
            if ev.get("직전값") and ev["직전값"] != "-":
                details.append(f"직전 {ev['직전값']}")
            if ev.get("예상값") and ev["예상값"] != "-":
                details.append(f"예상 {ev['예상값']}")
            detail_str = "  " + " · ".join(details) if details else ""

            items_html += f"""
<div style="display:flex;align-items:flex-start;gap:12px;
     background:#111318;border:1px solid #1E2129;border-left:3px solid {color};
     border-radius:8px;padding:10px 14px;margin-bottom:6px;">
  <div style="font-size:12px;color:#6B7280;min-width:70px;padding-top:2px;">{ev['시간_KST']}</div>
  <div style="flex:1;">
    <div style="font-size:13px;font-weight:600;color:#F3F4F6;">{ev['항목']}{speaker}</div>
    <div style="font-size:11px;color:#6B7280;margin-top:2px;">
      <span style="background:{color}22;color:{color};border-radius:4px;padding:1px 7px;font-size:10px;">{cat}</span>
      {detail_str}
    </div>
  </div>
</div>"""

        components.html(f"""
<html><head><link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet"><style>*{{margin:0;padding:0;box-sizing:border-box;font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}body{{background:transparent;}}</style></head>
<body>{items_html}</body></html>""", height=min(len(next_events) * 72 + 10, 420), scrolling=True)
    else:
        st.info("향후 24시간 내 예정된 이벤트가 없습니다.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── 달력 + 날짜 상세 ──────────────────────────────────────
    today = date.today()
    cal_col, detail_col = st.columns([3, 2])

    with cal_col:
        year, month = today.year, today.month
        st.markdown(
            f"<div style='font-size:13px;font-weight:600;color:#9CA3AF;margin-bottom:10px;'>"
            f"📅 {year}년 {month}월 경제 캘린더</div>",
            unsafe_allow_html=True,
        )
        event_counts = get_event_count_by_date(year, month)
        _, last_day = cal_mod.monthrange(year, month)
        first_weekday = (date(year, month, 1).weekday() + 1) % 7

        cal_html = _build_calendar_html(year, month, last_day, first_weekday, event_counts, today, CATEGORY_COLORS)
        components.html(cal_html, height=340, scrolling=False)

    with detail_col:
        selected_date = st.date_input("날짜 선택", value=today, key="cal_date", label_visibility="collapsed")
        events = get_events_for_date(selected_date)

        st.markdown(
            f"<div style='font-size:13px;font-weight:600;color:#9CA3AF;margin-bottom:8px;'>"
            f"📌 {selected_date.strftime('%m월 %d일')} ({len(events)}건)</div>",
            unsafe_allow_html=True,
        )

        if events:
            for ev in sorted(events, key=lambda x: x["시간_KST"]):
                cat = ev["카테고리"]
                color = _TAG_COLORS.get(cat, "#6B7280")
                with st.container(border=True):
                    st.markdown(
                        f"<div style='font-size:13px;font-weight:600;color:#F3F4F6;margin-bottom:4px;'>{ev['항목']}</div>"
                        f"<div style='font-size:11px;color:#6B7280;'>"
                        f"⏰ {ev['시간_KST']} KST &nbsp;·&nbsp; "
                        f"<span style='background:{color}22;color:{color};border-radius:4px;padding:1px 6px;'>{cat}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    items = []
                    if ev.get("직전값") and ev["직전값"] != "-": items.append(f"직전: **{ev['직전값']}**")
                    if ev.get("예상값") and ev["예상값"] != "-": items.append(f"예상: **{ev['예상값']}**")
                    if ev.get("인사정보"): items.append(f"성향: {ev['인사정보']}")
                    if items:
                        st.markdown(" &nbsp;·&nbsp; ".join(items))
        else:
            st.markdown("<div style='color:#4B5563;font-size:13px;padding:20px 0;'>예정된 이벤트 없음</div>", unsafe_allow_html=True)


def _build_calendar_html(year, month, last_day, first_weekday, event_counts, today, cat_colors):
    css = """
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0D1117;padding:2px;}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;}
.hdr{text-align:center;font-size:10px;font-weight:700;color:#4B5563;padding:5px 0;}
.cell{min-height:44px;border-radius:7px;padding:4px 5px;border:1px solid #1E2129;background:#111318;}
.cell.today{border:1.5px solid #A78BFA;background:#1A1830;}
.cell.empty{border:none;background:transparent;}
.num{font-size:11px;font-weight:700;color:#9CA3AF;}
.cell.today .num{color:#A78BFA;}
.dots{display:flex;flex-wrap:wrap;gap:2px;margin-top:3px;}
.dot{width:5px;height:5px;border-radius:50%;}
</style>"""
    days = "".join(f'<div class="hdr">{d}</div>' for d in ["일", "월", "화", "수", "목", "금", "토"])
    cells = "".join('<div class="cell empty"></div>' for _ in range(first_weekday))

    for day in range(1, last_day + 1):
        d = date(year, month, day)
        is_today = "today" if d == today else ""
        cats = event_counts.get(d.isoformat(), {})
        dots = "".join(
            f'<span class="dot" style="background:{cat_colors.get(c,"#6B7280")};"></span>'
            for c, cnt in cats.items() for _ in range(min(cnt, 3))
        )
        cells += f'<div class="cell {is_today}"><div class="num">{day}</div><div class="dots">{dots}</div></div>'

    return f"<html><head>{css}</head><body><div class='grid'>{days}{cells}</div></body></html>"


# ═════════════════════════════════════════════════════════════════════════════
# 포트폴리오
# ═════════════════════════════════════════════════════════════════════════════
def render_portfolio():
    from portfolio.manager import PortfolioManager
    pm = PortfolioManager()
    status = pm.get_status_summary()

    section_title("01", "포트폴리오 현황", "Portfolio Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("총 자산", f"${status['total_value']:,.2f}")
    c2.metric("현금", f"${status['cash']:,.2f}")
    c3.metric("보유종목 가치", f"${status['holdings_value']:,.2f}")

    section_title("02", "보유 종목", "Holdings")
    if status["holdings"]:
        df = pd.DataFrame(status["holdings"])
        df["합계"] = df["quantity"] * df["avg_price"]
        df.columns = ["종목", "수량", "평균단가", "합계"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("보유 종목이 없습니다.")

    section_title("03", "최근 거래 이력", "Recent Transactions")
    txns = pm.get_recent_transactions(limit=20)
    if txns:
        st.dataframe(pd.DataFrame(txns), use_container_width=True, hide_index=True)
    else:
        st.info("거래 이력이 없습니다.")


# ═════════════════════════════════════════════════════════════════════════════
# 보고서
# ═════════════════════════════════════════════════════════════════════════════
def render_reports():
    from reports.generator import ReportGenerator
    rg = ReportGenerator()
    section_title("01", "일일 보고서", "Daily Report")
    reports = rg.list_reports(limit=30)
    if not reports:
        st.info("아직 보고서가 없습니다.")
        return
    selected = st.selectbox("보고서 선택", [r["filename"] for r in reports])
    if selected:
        content = rg.read_report(selected)
        if content:
            st.markdown(content)
        else:
            st.error("보고서를 읽을 수 없습니다.")


# ═════════════════════════════════════════════════════════════════════════════
# 단일 화면 — 시황 브리핑
# ═════════════════════════════════════════════════════════════════════════════
render_briefing()
