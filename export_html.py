"""시황 브리핑 → 정적 HTML 리포트 내보내기

서버·WebSocket 없이 어떤 브라우저(카카오톡 인앱 브라우저 포함)에서도 열리는
자체 완결형(self-contained) 반응형 HTML을 생성한다.

사용법:
    python export_html.py                 # reports/ 에 타임스탬프 파일 생성
    python export_html.py --open          # 생성 후 기본 브라우저로 열기
    python export_html.py -o out.html     # 출력 경로 지정
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.briefing import (
    get_market_session_info,
    get_fear_greed_index,
    get_market_indices,
    get_japan_rates,
    get_put_call_ratio,
    get_options_chains,
)
from data.calendar_data import (
    get_events_next_24h,
    get_events_for_range,
    CATEGORY_COLORS,
    CALENDAR_EVENTS,
)

KST = timezone(timedelta(hours=9))

# 가격 변동 색상 (미국 관례: 상승=초록, 하락=빨강)
UP = "#4ADE80"
DOWN = "#F87171"
FLAT = "#9CA3AF"


def esc(v) -> str:
    return html.escape(str(v))


def fmt_num(v) -> str:
    """천단위 콤마 + 소수 둘째자리."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return esc(v)
    if abs(f) >= 1000:
        return f"{f:,.2f}"
    return f"{f:.2f}"


def sign_color(v) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return FLAT
    return UP if f > 0 else DOWN if f < 0 else FLAT


def sign_prefix(v) -> str:
    try:
        return "+" if float(v) > 0 else ""
    except (TypeError, ValueError):
        return ""


def score_color(s) -> str:
    """공포탐욕 점수 → 색상."""
    try:
        s = float(s)
    except (TypeError, ValueError):
        return FLAT
    if s >= 75:
        return "#10B981"
    if s >= 55:
        return "#84CC16"
    if s >= 45:
        return "#FBBF24"
    if s >= 25:
        return "#FB923C"
    return "#EF4444"


# ──────────────────────────────────────────────────────────────────────────
# SVG 차트 (순수 SVG — JS·외부 의존성 없음, 모든 브라우저 호환)
# ──────────────────────────────────────────────────────────────────────────
def fg_gauge_svg(score: float, grade: str, color: str) -> str:
    """공포탐욕 반원 게이지."""
    import math
    cx, cy, R = 200, 188, 150

    def polar(s, r=R):
        a = math.radians(180 - 1.8 * max(0, min(100, s)))
        return (cx + r * math.cos(a), cy - r * math.sin(a))

    def arc(s0, s1, r=R):
        x0, y0 = polar(s0, r)
        x1, y1 = polar(s1, r)
        return f"M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}"

    zones = [(0, 25, "#6E2A2A"), (25, 45, "#6E4A24"), (45, 55, "#5E5E2C"),
             (55, 75, "#2C5E3C"), (75, 100, "#1F6E47")]
    bg = "".join(f'<path d="{arc(a,b)}" stroke="{col}" stroke-width="26" fill="none"/>'
                 for a, b, col in zones)
    val = f'<path d="{arc(0, score)}" stroke="{color}" stroke-width="26" fill="none" stroke-linecap="round"/>'

    lab_svg = ""
    for s, t in [(2, "극공포"), (22, "공포"), (50, "중립"), (78, "탐욕"), (98, "극탐욕")]:
        lx, ly = polar(s, R + 24)
        anchor = "start" if s < 15 else "end" if s > 85 else "middle"
        lab_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#6B7280" font-size="12" text-anchor="{anchor}">{t}</text>'

    return f"""<svg viewBox="0 0 400 232" style="width:100%;height:auto;display:block;" xmlns="http://www.w3.org/2000/svg">
{bg}{val}{lab_svg}
<text x="200" y="176" fill="{color}" font-size="48" font-weight="800" text-anchor="middle">{score:.0f}</text>
<text x="200" y="210" fill="{color}" font-size="15" font-weight="700" text-anchor="middle">{esc(grade)}</text>
</svg>"""


def fg_timeline_svg(timeline: list) -> str:
    """공포탐욕 1년 타임라인 라인차트."""
    if not timeline or len(timeline) < 2:
        return ""
    from datetime import datetime as _dt, timedelta as _td
    W, H = 760, 212
    L, Rr, T, B = 46, 748, 16, 176
    pts = timeline
    n = len(pts)

    def X(i):
        return L + (Rr - L) * (i / (n - 1))

    def Y(s):
        return B - (B - T) * (max(0, min(100, s)) / 100)

    poly = " ".join(f"{X(i):.1f},{Y(p['score']):.1f}" for i, p in enumerate(pts))
    # 면적 채우기 경로
    area = f"M{X(0):.1f},{B} " + " ".join(f"L{X(i):.1f},{Y(p['score']):.1f}" for i, p in enumerate(pts)) + f" L{X(n-1):.1f},{B} Z"

    grid = ""
    for s, lab, col in [(75, "탐욕", "#10B981"), (50, "중립", "#6B7280"), (25, "공포", "#EF4444")]:
        y = Y(s)
        grid += (f'<line x1="{L}" y1="{y:.1f}" x2="{Rr}" y2="{y:.1f}" stroke="{col}" '
                 f'stroke-width="1" stroke-dasharray="4 4" opacity="0.45"/>'
                 f'<text x="{L-6}" y="{y+3:.1f}" fill="{col}" font-size="10" text-anchor="end">{lab}</text>')

    xlab = ""
    prev_m = None
    for i, p in enumerate(pts):
        d = _dt.strptime(p["date"], "%Y-%m-%d")
        if d.month != prev_m:
            prev_m = d.month
            xlab += (f'<line x1="{X(i):.1f}" y1="{T}" x2="{X(i):.1f}" y2="{B}" stroke="#1E2129" stroke-width="1"/>'
                     f'<text x="{X(i):.1f}" y="{H-4}" fill="#6B7280" font-size="10" text-anchor="middle">{d.year%100:02d}.{d.month:02d}</text>')

    last_d = _dt.strptime(pts[-1]["date"], "%Y-%m-%d")

    def nearest(days):
        target = last_d - _td(days=days)
        best, bd = 0, 10 ** 9
        for i, p in enumerate(pts):
            dd = abs((_dt.strptime(p["date"], "%Y-%m-%d") - target).days)
            if dd < bd:
                bd, best = dd, i
        return best

    marks, seen = "", set()
    for days in [365, 180, 90, 30, 7, 0]:
        i = (n - 1) if days == 0 else nearest(days)
        if i in seen:
            continue
        seen.add(i)
        p = pts[i]
        col = score_color(p["score"])
        marks += (f'<circle cx="{X(i):.1f}" cy="{Y(p["score"]):.1f}" r="4" fill="{col}" stroke="#0B0D12" stroke-width="1.5"/>'
                  f'<text x="{X(i):.1f}" y="{Y(p["score"])-9:.1f}" fill="#D1D5DB" font-size="10" font-weight="600" text-anchor="middle">{p["score"]:.0f}</text>')

    return f"""<svg viewBox="0 0 {W} {H}" style="width:100%;height:auto;display:block;" xmlns="http://www.w3.org/2000/svg">
<path d="{area}" fill="#A78BFA" opacity="0.08"/>
{grid}{xlab}
<polyline points="{poly}" fill="none" stroke="#A78BFA" stroke-width="1.8" stroke-linejoin="round"/>
{marks}
</svg>"""


def oi_chart_svg(ch: dict) -> str:
    """만기별 행사가 OI 다이버징 바차트 (Put=좌/적, Call=우/녹) + 핵심 레벨 기준선."""
    rows = ch.get("행사가") or []
    if not rows:
        return ""
    n = len(rows)
    W, top, rh, bot = 760, 12, 15, 16
    H = top + n * rh + bot
    Lx, Rx = 40, 752
    center = (Lx + Rx) / 2
    maxoi = max((max(r["call_oi"], r["put_oi"]) for r in rows), default=1) or 1
    callmax, putmax = Rx - center - 4, center - Lx - 4
    smax, smin = rows[0]["strike"], rows[-1]["strike"]

    def yrow(i):
        return top + i * rh + rh / 2

    def yprice(p):
        if smax == smin:
            return yrow(0)
        p = max(min(p, smax), smin)
        return yrow(0) + (smax - p) / (smax - smin) * (yrow(n - 1) - yrow(0))

    bars = ""
    bh = rh * 0.66
    for i, r in enumerate(rows):
        y = yrow(i)
        cl = r["call_oi"] / maxoi * callmax
        pl = r["put_oi"] / maxoi * putmax
        bars += (f'<rect x="{center:.1f}" y="{y-bh/2:.1f}" width="{cl:.1f}" height="{bh:.1f}" fill="#4ADE80" opacity="0.82"/>'
                 f'<rect x="{center-pl:.1f}" y="{y-bh/2:.1f}" width="{pl:.1f}" height="{bh:.1f}" fill="#F87171" opacity="0.82"/>'
                 f'<text x="{center:.1f}" y="{y+3:.1f}" fill="#9CA3AF" font-size="9" text-anchor="middle">{r["strike"]:.0f}</text>')

    axis = f'<line x1="{center}" y1="{top-2}" x2="{center}" y2="{top+n*rh:.1f}" stroke="#374151" stroke-width="1"/>'

    refs = ""
    for p, col, dash in [(ch["현재가"], "#FFFFFF", "0"), (ch["맥스페인"], "#FBBF24", "3 3"),
                         (ch["콜월"], "#4ADE80", "6 3"), (ch["풋월"], "#F87171", "6 3")]:
        if p is None:
            continue
        y = yprice(p)
        refs += f'<line x1="{Lx}" y1="{y:.1f}" x2="{Rx}" y2="{y:.1f}" stroke="{col}" stroke-width="1" stroke-dasharray="{dash}" opacity="0.55"/>'

    return f"""<svg viewBox="0 0 {W} {H:.0f}" style="width:100%;height:auto;display:block;" xmlns="http://www.w3.org/2000/svg">
{refs}{axis}{bars}
</svg>"""


# ──────────────────────────────────────────────────────────────────────────
# 섹션 빌더
# ──────────────────────────────────────────────────────────────────────────
def build_header(session: dict) -> str:
    sess = session["현재_세션"]
    is_open = "정규장" in sess
    is_pre = "프리" in sess
    color = UP if is_open else "#FBBF24" if is_pre else FLAT
    return f"""
<div class="hero">
  <div class="hero-top">
    <div>
      <h1>미국 증시 시황 브리핑</h1>
      <p class="sub">US Market Briefing</p>
    </div>
    <span class="badge" style="color:{color};border-color:{color}55;background:{color}1a;">
      ● {esc(sess)}
    </span>
  </div>
  <div class="hero-meta">
    <span>🇰🇷 {esc(session['현재시각_한국'])}</span>
    <span>🇺🇸 {esc(session['현재시각_미국'])}</span>
  </div>
</div>"""


def build_session_timeline(session: dict) -> str:
    rows = ""
    cur = session["현재_세션"]
    for name, info in session["세션정보"].items():
        active = name == cur
        dot = UP if active else "#374151"
        rows += f"""
    <div class="srow{' active' if active else ''}">
      <span class="sdot" style="background:{dot};"></span>
      <span class="sname">{esc(name)}</span>
      <span class="stime">미국 {esc(info['start'])}–{esc(info['end'])}</span>
      <span class="skst">한국 {esc(info['start_kst'])}–{esc(info['end_kst'])}</span>
    </div>"""
    return f"""
<section>
  <div class="sec-title"><span class="num">00</span>거래 세션 시간 <em>Market Sessions</em></div>
  <div class="card">{rows}
  </div>
</section>"""


def build_indices(indices: list, jp: dict) -> str:
    cards = ""
    for it in indices:
        if it.get("에러"):
            continue
        unit = it.get("단위", "")
        col = sign_color(it["변동률"])
        cards += f"""
    <div class="idx">
      <div class="idx-name">{esc(it['이름'])}</div>
      <div class="idx-price">{fmt_num(it['현재가'])}<span class="unit">{esc(unit)}</span></div>
      <div class="idx-chg" style="color:{col};">
        {sign_prefix(it['전일대비'])}{fmt_num(it['전일대비'])} ({sign_prefix(it['변동률'])}{fmt_num(it['변동률'])}%)
      </div>
    </div>"""

    # 일본 금리 (참고)
    base = jp.get("일본_기준금리", {})
    y10 = jp.get("일본_10년물_국채금리", {})
    y10v = f'{fmt_num(y10.get("값"))}' if y10.get("값") is not None else "—"
    cards += f"""
    <div class="idx">
      <div class="idx-name">일본 기준금리</div>
      <div class="idx-price">{fmt_num(base.get('값'))}<span class="unit">%</span></div>
      <div class="idx-chg" style="color:var(--t3);">BOJ 정책금리</div>
    </div>
    <div class="idx">
      <div class="idx-name">일본 10년물 국채</div>
      <div class="idx-price">{y10v}<span class="unit">%</span></div>
      <div class="idx-chg" style="color:var(--t3);">JGB 10Y</div>
    </div>"""

    return f"""
<section>
  <div class="sec-title"><span class="num">01</span>주요 지수 · 금리 · 원자재 <em>Market Overview</em></div>
  <div class="grid idx-grid">{cards}
  </div>
</section>"""


def build_fear_greed(fg: dict) -> str:
    score = fg.get("현재점수", 50)
    grade = fg.get("등급", "")
    c = score_color(score)

    gauge = fg_gauge_svg(score, grade, c)
    timeline = fg_timeline_svg(fg.get("타임라인") or [])

    hist = ""
    for label, key in [("1주 전", "1주전"), ("1개월 전", "1개월전"),
                       ("3개월 전", "3개월전"), ("6개월 전", "6개월전"), ("1년 전", "1년전")]:
        v = fg.get(key)
        if v is not None:
            hist += f'<div class="hg"><span>{label}</span><b style="color:{score_color(v)};">{fmt_num(v)}</b></div>'

    indicators = ""
    for name, d in (fg.get("세부지표") or {}).items():
        if isinstance(d, dict) and d.get("score") is not None:
            sc = d.get("score")
            indicators += f"""
      <div class="indi">
        <span class="indi-name">{esc(name)}</span>
        <span class="indi-bar"><span class="indi-fill" style="width:{max(0,min(100,sc))}%;background:{score_color(sc)};"></span></span>
        <span class="indi-val">{fmt_num(sc)}</span>
      </div>"""

    err = f'<p class="err">⚠ {esc(fg["에러"])}</p>' if fg.get("에러") else ""
    timeline_card = (f'<div class="card" style="margin-top:10px;">'
                     f'<div class="sub-head">최근 1년 추이</div>{timeline}</div>') if timeline else ""
    return f"""
<section>
  <div class="sec-title"><span class="num">02</span>공포탐욕지수 <em>Fear &amp; Greed</em></div>
  <div class="card">
    <div class="gauge-wrap">{gauge}</div>
    <div class="fg-hist">{hist}</div>
  </div>
  {timeline_card}
  {f'<div class="card indi-wrap"><div class="sub-head">세부 지표</div>{indicators}</div>' if indicators else ''}
  {err}
</section>"""


def build_pcr(pcr: dict, chains: dict) -> str:
    pc = pcr.get("풋콜비율")
    pc_html = (f'<b>{fmt_num(pc)}</b> <span class="muted">{esc(pcr.get("등급",""))}</span>'
               if pc is not None else '<span class="muted">조회 실패</span>')
    ticker = chains.get("티커", "QQQ")
    spot = chains.get("현재가")
    summary = f"""
  <div class="card kv" style="margin-bottom:12px;">
    <div class="kv-label">시장심리 풋/콜 (CNN F&amp;G)</div>
    <div class="kv-val">{pc_html}</div>
    <div class="kv-note">{esc(pcr.get("비고",""))} · 옵션 분석 기준: {esc(ticker)} 현재가 {fmt_num(spot) if spot else '—'}</div>
  </div>"""

    exps = chains.get("만기목록") or []
    if not exps:
        body = '<p class="muted">옵션 체인 데이터를 불러올 수 없습니다.</p>'
    else:
        titles = ["1차 만기 (최근접)", "2차 만기", "3차 만기", "4차 만기"]
        cards = ""
        for i, ch in enumerate(exps[:4]):
            legend = (
                f'<span class="lg"><i style="background:#FFFFFF;"></i>Spot {fmt_num(ch["현재가"])}</span>'
                f'<span class="lg"><i style="background:#FBBF24;"></i>Max Pain {fmt_num(ch["맥스페인"])}</span>'
                f'<span class="lg"><i style="background:#4ADE80;"></i>Call Wall {fmt_num(ch["콜월"])}</span>'
                f'<span class="lg"><i style="background:#F87171;"></i>Put Wall {fmt_num(ch["풋월"])}</span>'
            )
            pcr_col = "#F87171" if ch["PCR"] >= 1 else "#4ADE80"
            cards += f"""
    <div class="card oi">
      <div class="oi-head">
        <span class="oi-title">{esc(titles[i])}</span>
        <span class="oi-exp">{esc(ch['만기'])} · PCR <b style="color:{pcr_col};">{fmt_num(ch['PCR'])}</b></span>
      </div>
      <div class="oi-legend">{legend}</div>
      <div class="oi-axislab"><span style="color:#F87171;">◀ Put</span><span style="color:#4ADE80;">Call ▶</span></div>
      {oi_chart_svg(ch)}
    </div>"""
        body = f'<div class="grid g2">{cards}</div>'

    return f"""
<section>
  <div class="sec-title"><span class="num">03</span>풋/콜 비율 <em>Put / Call Ratio</em></div>
  {summary}
  {body}
</section>"""


def build_calendar() -> str:
    now = datetime.now(KST)
    # 향후 24시간
    nx = get_events_next_24h()
    nx_html = ""
    if nx:
        for ev in sorted(nx, key=lambda x: x["시간_KST"]):
            cat = ev["카테고리"]
            col = CATEGORY_COLORS.get(cat, "#6B7280")
            sp = f" · {esc(ev['인사정보'])}" if ev.get("인사정보") else ""
            nx_html += f"""
      <div class="evt" style="border-left-color:{col};">
        <span class="evt-time">{esc(ev['시간_KST'])}</span>
        <span class="evt-name">{esc(ev['항목'])}{sp}</span>
        <span class="evt-cat" style="color:{col};background:{col}22;">{esc(cat)}</span>
      </div>"""
    else:
        nx_html = '<p class="muted" style="padding:6px 2px;">향후 24시간 내 예정된 이벤트가 없습니다.</p>'

    # 전체 이벤트를 날짜별로 묶어 JS로 전달 (월 전환 시 클라이언트에서 렌더)
    ev_map: dict = {}
    for e in CALENDAR_EVENTS:
        cat = e["카테고리"]
        sp = f" · {e['인사정보']}" if e.get("인사정보") else ""
        ev_map.setdefault(e["날짜"], []).append({
            "time": e["시간_KST"],
            "name": e["항목"] + sp,
            "cat": cat,
            "color": CATEGORY_COLORS.get(cat, "#6B7280"),
        })
    for d in ev_map:
        ev_map[d].sort(key=lambda x: x["time"])

    events_json = json.dumps(ev_map, ensure_ascii=False)
    today_str = now.strftime("%Y-%m-%d")

    return f"""
<section>
  <div class="sec-title"><span class="num">04</span>경제 캘린더 <em>Economic Calendar</em></div>
  <div class="card">
    <div class="sub-head">⏰ 향후 24시간</div>{nx_html}
  </div>
  <div class="card" style="margin-top:14px;">
    <div class="cal-head">
      <button type="button" id="cal-prev" aria-label="이전 달">‹</button>
      <span id="cal-label"></span>
      <button type="button" id="cal-next" aria-label="다음 달">›</button>
    </div>
    <div class="cal-grid" id="cal-grid"></div>
  </div>
  <div class="cal-detail" id="cal-detail"></div>
</section>
<script>
(function(){{
  var EVENTS = {events_json};
  var TODAY = "{today_str}";
  var WD = ["일","월","화","수","목","금","토"];
  var parts = TODAY.split("-");
  var curY = parseInt(parts[0],10), curM = parseInt(parts[1],10);
  var selected = TODAY;
  function pad(n){{ return (n<10?"0":"")+n; }}
  function render(){{
    document.getElementById("cal-label").textContent = curY + "년 " + curM + "월";
    var first = new Date(curY, curM-1, 1).getDay();
    var days = new Date(curY, curM, 0).getDate();
    var html = "";
    for(var i=0;i<7;i++){{ html += '<div class="cal-wd'+(i===0?" sun":i===6?" sat":"")+'">'+WD[i]+'</div>'; }}
    for(var e=0;e<first;e++){{ html += '<div class="cal-cell empty"></div>'; }}
    for(var d=1; d<=days; d++){{
      var ds = curY+"-"+pad(curM)+"-"+pad(d);
      var evs = EVENTS[ds] || [];
      var cls = "cal-cell" + (evs.length?" has":"") + (ds===TODAY?" today":"") + (ds===selected?" sel":"");
      var dots = "";
      var seen = {{}}, cnt = 0;
      for(var k=0;k<evs.length;k++){{ var c=evs[k].color; if(!seen[c] && cnt<4){{ seen[c]=1; cnt++; dots += '<span class="dot" style="background:'+c+'"></span>'; }} }}
      html += '<div class="'+cls+'" data-d="'+ds+'">'
            + '<span class="dnum">'+d+'</span>'
            + (evs.length?'<span class="cnt">'+evs.length+'</span>':'')
            + '<span class="dots">'+dots+'</span></div>';
    }}
    var grid = document.getElementById("cal-grid");
    grid.innerHTML = html;
    var cells = grid.querySelectorAll(".cal-cell:not(.empty)");
    for(var n=0;n<cells.length;n++){{
      cells[n].addEventListener("click", function(){{ selected = this.getAttribute("data-d"); render(); detail(); }});
    }}
  }}
  function detail(){{
    var box = document.getElementById("cal-detail");
    var evs = EVENTS[selected] || [];
    var dt = new Date(selected+"T00:00:00");
    var head = (dt.getMonth()+1)+"월 "+dt.getDate()+"일 ("+WD[dt.getDay()]+")";
    if(!evs.length){{ box.innerHTML = '<div class="cal-dhead">'+head+'</div><p class="muted">예정된 이벤트가 없습니다.</p>'; return; }}
    var h = '<div class="cal-dhead">'+head+' · '+evs.length+'건</div>';
    for(var i=0;i<evs.length;i++){{ var ev=evs[i];
      h += '<div class="evt" style="border-left-color:'+ev.color+';">'
         + '<span class="evt-time">'+ev.time+'</span>'
         + '<span class="evt-name">'+ev.name+'</span>'
         + '<span class="evt-cat" style="color:'+ev.color+';background:'+ev.color+'22;">'+ev.cat+'</span></div>';
    }}
    box.innerHTML = h;
  }}
  document.getElementById("cal-prev").addEventListener("click", function(){{ curM--; if(curM<1){{curM=12;curY--;}} render(); }});
  document.getElementById("cal-next").addEventListener("click", function(){{ curM++; if(curM>12){{curM=1;curY++;}} render(); }});
  render(); detail();
}})();
</script>"""


# ──────────────────────────────────────────────────────────────────────────
# CSS — 760px / 720px 반응형 / 다크 테마
# ──────────────────────────────────────────────────────────────────────────
CSS = """
:root{
  --bg:#0B0D12; --card:#111318; --border:#1E2129;
  --t1:#F3F4F6; --t2:#9CA3AF; --t3:#6B7280; --t4:#4B5563;
}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{background:var(--bg);color:var(--t1);
  font-family:'Pretendard',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  -webkit-text-size-adjust:100%;}
.page{max-width:760px;margin:0 auto;padding:24px 20px 80px;}
section{margin-top:28px;}
.sec-title{display:flex;align-items:center;gap:9px;margin-bottom:12px;font-size:15px;font-weight:700;
  background:linear-gradient(90deg,#60A5FA,#93C5FD);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;}
.sec-title .num{background:linear-gradient(135deg,#1D4ED8,#2563EB);color:#fff;font-size:10px;
  font-weight:700;padding:2px 8px;border-radius:20px;-webkit-text-fill-color:#fff;}
.sec-title em{font-style:normal;font-size:12px;color:var(--t4);-webkit-text-fill-color:var(--t4);font-weight:400;}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px 18px;}
.muted{color:var(--t3);font-size:12px;}
.err{color:#FBBF24;font-size:12px;margin-top:8px;}
.sub-head{font-size:13px;font-weight:600;color:var(--t2);margin-bottom:10px;}

/* HERO */
.hero{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px 22px;}
.hero-top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;}
.hero h1{font-size:26px;font-weight:900;letter-spacing:-0.5px;
  background:linear-gradient(90deg,#A78BFA,#60A5FA);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.hero .sub{font-size:12px;color:var(--t4);margin-top:3px;}
.badge{font-size:12px;font-weight:700;padding:5px 12px;border-radius:20px;border:1px solid;white-space:nowrap;}
.hero-meta{display:flex;gap:16px;flex-wrap:wrap;margin-top:14px;font-size:12px;color:var(--t2);}

/* SESSION */
.srow{display:flex;align-items:center;gap:10px;padding:9px 4px;border-bottom:1px solid var(--border);flex-wrap:wrap;}
.srow:last-child{border-bottom:none;}
.srow.active{font-weight:700;}
.sdot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
.sname{font-size:13px;flex:1;min-width:120px;}
.stime,.skst{font-size:12px;color:var(--t3);}
.skst{color:var(--t2);}

/* INDICES */
.grid{display:grid;gap:10px;}
.idx-grid{grid-template-columns:repeat(4,1fr);}
.idx{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:13px 14px;}
.idx-name{font-size:12px;color:var(--t2);margin-bottom:7px;height:30px;line-height:1.25;}
.idx-price{font-size:18px;font-weight:800;}
.idx-price .unit{font-size:11px;color:var(--t3);margin-left:2px;font-weight:500;}
.idx-chg{font-size:12px;font-weight:600;margin-top:4px;}

/* FEAR & GREED */
.g2{grid-template-columns:repeat(2,1fr);}
.gauge-wrap{max-width:400px;margin:0 auto;}
.fg-hist{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:6px;
  border-top:1px solid var(--border);padding-top:14px;}
.hg{text-align:center;font-size:11px;color:var(--t3);flex:1;min-width:56px;}
.hg b{display:block;font-size:15px;color:var(--t1);margin-top:3px;}
.indi-wrap{margin-top:10px;display:flex;flex-direction:column;gap:9px;}
.indi{display:flex;align-items:center;gap:10px;}
.indi-name{font-size:12px;color:var(--t2);width:160px;flex-shrink:0;}
.indi-bar{flex:1;height:6px;background:#0B0D12;border-radius:3px;overflow:hidden;}
.indi-fill{display:block;height:100%;background:linear-gradient(90deg,#3B82F6,#60A5FA);border-radius:3px;}
.indi-val{font-size:12px;font-weight:700;width:42px;text-align:right;}

/* OI 차트 */
.oi-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:8px;flex-wrap:wrap;}
.oi-title{font-size:13px;font-weight:700;color:var(--t1);}
.oi-exp{font-size:11px;color:var(--t3);}
.oi-legend{display:flex;flex-wrap:wrap;gap:8px 12px;margin-bottom:6px;}
.oi-legend .lg{font-size:10px;color:var(--t2);display:inline-flex;align-items:center;gap:4px;}
.oi-legend .lg i{width:9px;height:2px;display:inline-block;border-radius:1px;}
.oi-axislab{display:flex;justify-content:space-between;font-size:10px;font-weight:600;margin-bottom:2px;}

/* KV */
.kv-label{font-size:12px;color:var(--t2);margin-bottom:6px;}
.kv-val{font-size:18px;font-weight:800;}
.kv-val b{font-weight:800;}
.kv-note{font-size:11px;color:var(--t4);margin-top:6px;line-height:1.4;}

/* CALENDAR */
.evt{display:flex;align-items:center;gap:10px;background:#0E1015;border:1px solid var(--border);
  border-left:3px solid #6B7280;border-radius:8px;padding:9px 12px;margin-bottom:6px;flex-wrap:wrap;}
.evt-time{font-size:12px;color:var(--t3);min-width:54px;}
.evt-name{font-size:13px;font-weight:600;color:var(--t1);flex:1;min-width:140px;}
.evt-cat{font-size:10px;border-radius:4px;padding:2px 7px;white-space:nowrap;}

/* 달력 그리드 */
.cal-head{display:flex;align-items:center;justify-content:center;gap:18px;margin-bottom:14px;}
.cal-head button{background:#1A1D24;border:1px solid var(--border);color:var(--t1);
  width:34px;height:34px;border-radius:9px;font-size:18px;line-height:1;cursor:pointer;
  font-family:inherit;transition:background .15s;}
.cal-head button:hover{background:#262A33;border-color:#3B82F6;}
#cal-label{font-size:15px;font-weight:700;color:var(--t1);min-width:120px;text-align:center;}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;}
.cal-wd{text-align:center;font-size:11px;color:var(--t3);padding:2px 0 4px;}
.cal-wd.sun{color:#F87171;}
.cal-wd.sat{color:#60A5FA;}
.cal-cell{position:relative;min-height:56px;background:#0E1015;border:1px solid var(--border);
  border-radius:8px;padding:6px;transition:border-color .12s;}
.cal-cell.empty{background:transparent;border:none;}
.cal-cell.has{cursor:pointer;}
.cal-cell.has:hover{border-color:#3B82F6;}
.cal-cell.today{border-color:#60A5FA;}
.cal-cell.sel{background:#16203A;border-color:#3B82F6;}
.cal-cell .dnum{font-size:12px;color:var(--t2);}
.cal-cell.today .dnum{color:#60A5FA;font-weight:700;}
.cal-cell .cnt{position:absolute;top:5px;right:5px;font-size:9px;background:#1D4ED8;color:#fff;
  border-radius:8px;padding:0 5px;line-height:14px;}
.cal-cell .dots{position:absolute;bottom:6px;left:6px;display:flex;gap:2px;}
.cal-cell .dots .dot{width:5px;height:5px;border-radius:50%;}
.cal-detail{margin-top:16px;}
.cal-dhead{font-size:13px;font-weight:700;color:var(--t1);margin-bottom:10px;}

/* FOOTER */
.foot{margin-top:40px;text-align:center;font-size:11px;color:var(--t4);line-height:1.7;}

/* ── 모바일 반응형 ── */
@media (max-width:720px){
  .page{padding:18px 14px 60px;}
  .idx-grid{grid-template-columns:repeat(2,1fr);}
  .g2{grid-template-columns:1fr;}
  .hero h1{font-size:22px;}
  .fg{justify-content:center;}
  .indi-name{width:120px;}
}
@media (max-width:480px){
  .cal-grid{gap:4px;}
  .cal-cell{min-height:46px;padding:4px;}
  .cal-cell .dnum{font-size:11px;}
  .cal-cell .cnt{font-size:8px;padding:0 4px;}
}
@media (max-width:420px){
  .idx-grid{grid-template-columns:1fr 1fr;}
  .skst{width:100%;}
}
"""


def _fetch(fn, validate, attempts: int = 3, delay: int = 3):
    """데이터 수집 함수를 재시도하며, 검증 통과 시 (결과, True), 아니면 (마지막결과, False)."""
    import time
    result = None
    for i in range(attempts):
        try:
            result = fn()
        except Exception:
            result = None
        try:
            ok = result is not None and validate(result)
        except Exception:
            ok = False
        if ok:
            return result, True
        if i < attempts - 1:
            time.sleep(delay)
    return result, False


# 핵심 데이터(누락 시 ⚠ 경고) vs 보조 데이터
CRITICAL_SOURCES = ("지수·금리", "공포탐욕", "풋/콜")


def build_status_footer(status: dict) -> str:
    parts = "".join(
        f'<span style="color:{"#4ADE80" if ok else "#F87171"};margin:0 6px;">'
        f'{"●" if ok else "○"} {esc(name)}</span>'
        for name, ok in status.items()
    )
    return f'<div style="margin-top:6px;">데이터 상태: {parts}</div>'


def build_html():
    """리포트 HTML과 수집 상태(status dict)를 반환한다."""
    session = get_market_session_info()  # 네트워크 불필요

    indices, ok_idx = _fetch(get_market_indices,
                             lambda r: any(not it.get("에러") for it in r))
    fg, ok_fg = _fetch(get_fear_greed_index, lambda r: not r.get("에러"))
    pcr, ok_pcr = _fetch(get_put_call_ratio, lambda r: r.get("풋콜비율") is not None)
    jp, ok_jp = _fetch(get_japan_rates,
                       lambda r: r.get("일본_10년물_국채금리", {}).get("값") is not None)
    chains, ok_ch = _fetch(lambda: get_options_chains("QQQ"),
                           lambda r: bool(r.get("만기목록")))

    status = {
        "지수·금리": ok_idx,
        "공포탐욕": ok_fg,
        "풋/콜": ok_pcr,
        "옵션체인": ok_ch,
        "일본금리": ok_jp,
    }

    now = datetime.now(KST)
    gen = now.strftime("%Y-%m-%d %H:%M KST")

    body = "".join([
        build_header(session),
        build_session_timeline(session),
        build_indices(indices or [], jp or {}),
        build_fear_greed(fg or {}),
        build_pcr(pcr or {}, chains or {}),
        build_calendar(),
    ])

    doc = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="format-detection" content="telephone=no">
<title>미국 증시 시황 브리핑 · {esc(gen)}</title>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.min.css" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="page">
  <div style="font-size:11px;color:var(--t2);letter-spacing:0.3px;margin-bottom:10px;">
    © 전세영 &nbsp;·&nbsp; <a href="mailto:coolboy30a@naver.com" style="color:var(--t2);text-decoration:none;">coolboy30a@naver.com</a>
  </div>
{body}
  <div class="foot">
    생성 시각 {esc(gen)} · 데이터 스냅샷<br>
    US Stock AI Agent — 정적 리포트 (서버 불필요, 모든 브라우저 호환)
    {build_status_footer(status)}
  </div>
</div>
</body>
</html>"""
    return doc, status


def main():
    ap = argparse.ArgumentParser(description="시황 브리핑 정적 HTML 내보내기")
    ap.add_argument("-o", "--output", default=None, help="출력 파일 경로")
    ap.add_argument("--open", action="store_true", help="생성 후 브라우저로 열기")
    args = ap.parse_args()

    print("데이터 수집 중… (yfinance · 공포탐욕 · 경제캘린더)")
    doc, status = build_html()

    if args.output:
        out = args.output
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    else:
        reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
        os.makedirs(reports_dir, exist_ok=True)
        stamp = datetime.now(KST).strftime("%Y%m%d_%H%M")
        out = os.path.join(reports_dir, f"시황브리핑_{stamp}.html")

    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)

    failed = [k for k, v in status.items() if not v]
    print(f"생성 완료: {out}  ({os.path.getsize(out):,} bytes)")
    print(f"  데이터 상태: {status}")
    if failed:
        print(f"  ⚠ 수집 실패: {', '.join(failed)}")

    if args.open:
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(out))


if __name__ == "__main__":
    main()
