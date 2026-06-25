"""뉴스 감성 분석 엔진"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from data.news import NewsDataClient


class SentimentAnalyzer:
    """뉴스 데이터를 종합하여 종목별 감성 판단을 제공한다."""

    def __init__(self, news_client: Optional[NewsDataClient] = None):
        self._client = news_client or NewsDataClient()

    def analyze_ticker(self, ticker: str, limit: int = 30) -> Dict[str, Any]:
        """단일 종목에 대한 감성 분석 결과를 반환한다."""
        summary = self._client.fetch_ticker_sentiment_summary(ticker, limit=limit)

        recommendation = self._derive_recommendation(
            summary["avg_sentiment"],
            summary["bullish_count"],
            summary["bearish_count"],
        )

        return {
            **summary,
            "recommendation": recommendation,
        }

    def analyze_multiple(
        self, tickers: List[str], limit_per_ticker: int = 20
    ) -> List[Dict[str, Any]]:
        """여러 종목의 감성 분석을 일괄 수행한다."""
        results = []
        for ticker in tickers:
            try:
                results.append(self.analyze_ticker(ticker, limit=limit_per_ticker))
            except Exception as e:
                results.append({"ticker": ticker, "error": str(e)})
        return results

    def analyze_market_mood(self, limit: int = 50) -> Dict[str, Any]:
        """시장 전체의 뉴스 감성 분위기를 분석한다."""
        articles = self._client.fetch_news_sentiment(
            topics=["economy_macro", "financial_markets"],
            limit=limit,
        )

        if not articles:
            return {
                "article_count": 0,
                "avg_sentiment": 0.0,
                "mood": "Neutral",
                "top_headlines": [],
            }

        scores = [a["overall_sentiment_score"] for a in articles]
        avg = sum(scores) / len(scores) if scores else 0.0

        if avg >= 0.15:
            mood = "Bullish"
        elif avg <= -0.15:
            mood = "Bearish"
        else:
            mood = "Neutral"

        top_headlines = [
            {"title": a["title"], "sentiment": a["overall_sentiment_label"]}
            for a in articles[:5]
        ]

        return {
            "article_count": len(articles),
            "avg_sentiment": round(avg, 4),
            "mood": mood,
            "top_headlines": top_headlines,
        }

    @staticmethod
    def _derive_recommendation(
        avg_score: float, bullish: int, bearish: int
    ) -> str:
        total = bullish + bearish
        if total == 0:
            return "데이터 부족 — 판단 보류"

        bullish_ratio = bullish / total

        if avg_score >= 0.25 and bullish_ratio >= 0.6:
            return "강한 매수 의견"
        if avg_score >= 0.10:
            return "매수 우세"
        if avg_score <= -0.25 and bullish_ratio <= 0.4:
            return "강한 매도 의견"
        if avg_score <= -0.10:
            return "매도 우세"
        return "중립 / 혼조"
