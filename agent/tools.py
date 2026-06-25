"""Claude Tool Use 도구 정의 (8개)"""

TOOLS = [
    {
        "name": "fetch_macro_indicators",
        "description": (
            "FRED API를 통해 미국의 최신 거시경제 지표를 조회합니다: "
            "T10Y2Y(장단기 금리차), UNRATE(실업률), VIXCLS(VIX 공포지수), "
            "DEXKOUS(원/달러 환율), FEDFUNDS(연방기금금리), CPIAUCSL(CPI). "
            "경제 국면 판별과 Kill Switch 체크를 위해 반드시 먼저 호출하세요."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "fetch_market_data",
        "description": (
            "Polygon.io API를 통해 특정 미국 주식의 최신 주가 데이터를 조회합니다. "
            "현재가, 전일 대비 변동률, 일봉 시가/고가/저가/종가/거래량을 반환합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "미국 주식 티커 심볼 (예: AAPL, MSFT, QQQ, TQQQ)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "run_technical_analysis",
        "description": (
            "특정 종목의 기술적 분석을 실행합니다. "
            "이동평균(SMA 20/50/200), RSI(14), MACD, 볼린저밴드, ADX 등의 "
            "지표를 계산하고 매수/매도 시그널을 도출합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "분석할 미국 주식 티커 심볼",
                },
                "days": {
                    "type": "integer",
                    "description": "분석에 사용할 일봉 데이터 기간 (기본값: 200)",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "analyze_news_sentiment",
        "description": (
            "Alpha Vantage News Sentiment API를 사용해 특정 종목 또는 "
            "시장 전체의 뉴스 감성을 분석합니다. "
            "Bullish/Bearish/Neutral 판단과 주요 헤드라인을 반환합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "분석할 티커 (비우면 시장 전체 분석)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_portfolio_status",
        "description": (
            "현재 포트폴리오의 보유 종목, 수량, 평균 단가, 현재 수익률, "
            "총 자산 가치를 조회합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "update_portfolio",
        "description": (
            "포트폴리오에 매수 또는 매도 거래를 기록합니다. "
            "경제 국면 분석과 투자 전략이 결정된 후에 호출하세요."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "거래할 종목 티커",
                },
                "action": {
                    "type": "string",
                    "enum": ["buy", "sell"],
                    "description": "매수(buy) 또는 매도(sell)",
                },
                "quantity": {
                    "type": "number",
                    "description": "거래 수량",
                },
                "price": {
                    "type": "number",
                    "description": "거래 가격 (USD)",
                },
                "reason": {
                    "type": "string",
                    "description": "거래 사유",
                },
            },
            "required": ["ticker", "action", "quantity", "price", "reason"],
        },
    },
    {
        "name": "send_alert_email",
        "description": (
            "중요한 시장 이벤트나 투자 전략 변경 시 이메일 알림을 발송합니다. "
            "Kill Switch 발동, 급등/급락, 매수/매도 시그널 등에 사용합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "이메일 제목",
                },
                "body": {
                    "type": "string",
                    "description": "이메일 본문 (마크다운 지원)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "description": "알림 우선순위",
                },
            },
            "required": ["subject", "body"],
        },
    },
    {
        "name": "save_daily_report",
        "description": (
            "오늘의 투자 분석 보고서를 마크다운(.md) 파일로 저장합니다. "
            "모든 분석이 끝난 후 반드시 이 도구를 호출하여 보고서를 저장하세요."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_content": {
                    "type": "string",
                    "description": "마크다운 형식의 투자 분석 보고서 전체 내용",
                },
            },
            "required": ["report_content"],
        },
    },
]
