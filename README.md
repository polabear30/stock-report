# US Stock AI Agent

Claude LLM 기반 미국 주식 종합 분석 에이전트. 거시경제 지표, 기술적 분석, 뉴스 감성을 통합 판단하여 투자 전략을 도출합니다.

## 기능

- **거시경제 분석**: FRED API를 통한 금리차, 실업률, VIX, 환율 조회 및 경제 국면 판별
- **기술적 분석**: SMA/EMA, RSI, MACD, 볼린저밴드 등 지표 계산 및 시그널 도출
- **뉴스 감성 분석**: Alpha Vantage를 통한 종목별/시장 전체 뉴스 감성 분석
- **포트폴리오 관리**: SQLite 기반 보유 종목, 거래 이력, 일별 스냅샷 관리
- **이메일 알림**: 급등/급락, Kill Switch 발동 시 이메일 자동 발송
- **대시보드**: Streamlit 기반 포트폴리오 시각화
- **스케줄러**: APScheduler로 매일 장 마감 후 자동 분석

## 설치

```bash
cd stock
pip install -r requirements.txt
```

## 설정

`.env.example`을 `.env`로 복사하고 API 키를 입력합니다:

```bash
cp .env.example .env
```

필요한 API 키:
- `ANTHROPIC_API_KEY` — [Anthropic Console](https://console.anthropic.com/)
- `POLYGON_API_KEY` — [Polygon.io](https://polygon.io/)
- `FRED_API_KEY` — [FRED API](https://fred.stlouisfed.org/docs/api/api_key.html)
- `ALPHA_VANTAGE_API_KEY` — [Alpha Vantage](https://www.alphavantage.co/support/#api-key)

## 사용법

### 즉시 분석 (한 번 실행)
```bash
python main.py --run-now
```

### 스케줄러 모드 (자동 반복 실행)
```bash
python main.py
```

### 커스텀 프롬프트로 분석
```bash
python main.py --run-now --prompt "NVDA와 TSLA를 집중 분석해 주세요"
```

### 대시보드 실행
```bash
streamlit run dashboard/app.py
```

## 프로젝트 구조

```
stock/
├── config/settings.py      # 환경변수 기반 설정 관리
├── data/
│   ├── market.py           # Polygon.io 주가 데이터
│   ├── macro.py            # FRED 거시경제 지표
│   └── news.py             # Alpha Vantage 뉴스/감성
├── analysis/
│   ├── technical.py        # 기술적 분석 엔진
│   ├── macro.py            # 거시경제 국면 분석
│   └── sentiment.py        # 뉴스 감성 분석
├── agent/
│   ├── tools.py            # Claude Tool 정의 (8개)
│   ├── prompts.py          # 시스템 프롬프트
│   └── engine.py           # Claude Agent 실행 엔진
├── portfolio/
│   ├── models.py           # SQLAlchemy ORM 모델
│   ├── manager.py          # 포트폴리오 CRUD
│   └── db.py               # DB 연결 관리
├── alerts/email.py         # 이메일 알림
├── reports/generator.py    # 일일 보고서 생성
├── dashboard/app.py        # Streamlit 대시보드
├── scheduler/jobs.py       # APScheduler 작업
└── main.py                 # 진입점
```
