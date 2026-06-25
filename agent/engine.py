"""Claude Agent 실행 엔진 — Tool Use 루프"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Any, Dict, List, Optional

import anthropic

from agent.prompts import SYSTEM_PROMPT
from agent.tools import TOOLS
from analysis.macro import MacroAnalyzer
from analysis.sentiment import SentimentAnalyzer
from analysis.technical import TechnicalAnalyzer
from config.settings import get_settings
from data.macro import MacroDataClient
from data.market import MarketDataClient
from data.news import NewsDataClient


class StockAgent:
    """Claude Tool Use 기반 종합 주식 분석 에이전트"""

    def __init__(self, settings=None):
        self._settings = settings or get_settings()
        self._client = anthropic.Anthropic(api_key=self._settings.anthropic_api_key)
        self._market = MarketDataClient(self._settings.polygon_api_key)
        self._macro = MacroDataClient(self._settings.fred_api_key)
        self._news = NewsDataClient(self._settings.alpha_vantage_api_key)
        self._tech = TechnicalAnalyzer()
        self._macro_analyzer = MacroAnalyzer()
        self._sentiment = SentimentAnalyzer(self._news)

        self._portfolio_manager = None  # lazy init
        self._alert_sender = None       # lazy init

    def _get_portfolio_manager(self):
        if self._portfolio_manager is None:
            from portfolio.manager import PortfolioManager
            self._portfolio_manager = PortfolioManager()
        return self._portfolio_manager

    def _get_alert_sender(self):
        if self._alert_sender is None:
            from alerts.email import EmailAlertSender
            self._alert_sender = EmailAlertSender()
        return self._alert_sender

    # ------------------------------------------------------------------
    # Tool 실행 디스패처
    # ------------------------------------------------------------------
    def _execute_tool(self, name: str, inputs: Dict[str, Any]) -> str:
        try:
            result = self._dispatch(name, inputs)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"error": f"{name} 실행 실패: {e}"}, ensure_ascii=False)

    def _dispatch(self, name: str, inputs: Dict) -> Any:
        if name == "fetch_macro_indicators":
            return self._tool_fetch_macro()
        if name == "fetch_market_data":
            return self._tool_fetch_market(inputs["ticker"])
        if name == "run_technical_analysis":
            return self._tool_technical(inputs["ticker"], inputs.get("days", 200))
        if name == "analyze_news_sentiment":
            return self._tool_sentiment(inputs.get("ticker"))
        if name == "get_portfolio_status":
            return self._tool_portfolio_status()
        if name == "update_portfolio":
            return self._tool_update_portfolio(inputs)
        if name == "send_alert_email":
            return self._tool_send_alert(inputs)
        if name == "save_daily_report":
            return self._tool_save_report(inputs["report_content"])
        raise ValueError(f"알 수 없는 도구: {name}")

    # ------------------------------------------------------------------
    # 개별 Tool 구현
    # ------------------------------------------------------------------
    def _tool_fetch_macro(self) -> Dict:
        indicators = self._macro.fetch_all_indicators()
        t10y2y = indicators.get("T10Y2Y", {}).get("value")
        unrate = indicators.get("UNRATE", {}).get("value")
        vix = indicators.get("VIXCLS", {}).get("value")
        usdkrw = indicators.get("DEXKOUS", {}).get("value")

        phase_result = self._macro_analyzer.classify_phase(t10y2y, unrate, vix, usdkrw)
        return {"indicators": indicators, "analysis": phase_result}

    def _tool_fetch_market(self, ticker: str) -> Dict:
        return self._market.get_snapshot(ticker)

    def _tool_technical(self, ticker: str, days: int = 200) -> Dict:
        df = self._market.get_daily_bars(ticker, days=days)
        if df.empty:
            return {"error": f"{ticker} 데이터를 가져올 수 없습니다"}
        signals = self._tech.generate_signals(df)
        return {"ticker": ticker, **signals}

    def _tool_sentiment(self, ticker: Optional[str] = None) -> Dict:
        if ticker:
            return self._sentiment.analyze_ticker(ticker)
        return self._sentiment.analyze_market_mood()

    def _tool_portfolio_status(self) -> Dict:
        pm = self._get_portfolio_manager()
        return pm.get_status_summary()

    def _tool_update_portfolio(self, inputs: Dict) -> Dict:
        pm = self._get_portfolio_manager()
        tx = pm.record_transaction(
            ticker=inputs["ticker"],
            action=inputs["action"],
            quantity=inputs["quantity"],
            price=inputs["price"],
            reason=inputs.get("reason", ""),
        )
        return {"status": "success", "transaction_id": tx.id, "message": f"{inputs['action']} {inputs['ticker']} x{inputs['quantity']} @ ${inputs['price']}"}

    def _tool_send_alert(self, inputs: Dict) -> Dict:
        sender = self._get_alert_sender()
        ok = sender.send(
            subject=inputs["subject"],
            body=inputs["body"],
            priority=inputs.get("priority", "normal"),
        )
        return {"status": "sent" if ok else "failed"}

    def _tool_save_report(self, content: str) -> Dict:
        from reports.generator import ReportGenerator
        gen = ReportGenerator()
        path = gen.save_daily_report(content)
        return {"status": "success", "filepath": path}

    # ------------------------------------------------------------------
    # 에이전트 메인 루프
    # ------------------------------------------------------------------
    def run(self, user_prompt: Optional[str] = None) -> str:
        """에이전트를 실행하고 최종 응답 텍스트를 반환한다."""
        if user_prompt is None:
            tickers = ", ".join(self._settings.watchlist_tickers)
            user_prompt = (
                f"오늘({date.today().isoformat()}) 미국 주식 시장을 종합 분석해 주세요.\n"
                f"관심 종목: {tickers}\n"
                "거시경제 지표를 조회하고, 각 종목의 기술적 분석과 뉴스 감성을 분석한 뒤, "
                "포트폴리오 조정 전략을 제시하고 보고서를 저장해 주세요."
            )

        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": user_prompt},
        ]

        max_iterations = 15

        for i in range(max_iterations):
            response = self._client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            for block in response.content:
                if block.type == "text" and block.text.strip():
                    print(f"\n  [Step {i + 1}] {block.text[:200]}...")

            if response.stop_reason == "end_turn":
                texts = [b.text for b in response.content if b.type == "text"]
                return "\n".join(texts)

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  [Tool] {block.name}({json.dumps(block.input, ensure_ascii=False)[:100]})")
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "user", "content": tool_results})

        return "[최대 반복 횟수 도달 — 분석 미완료]"
