"""Alpha Vantage News Sentiment API를 통한 뉴스/감성 데이터 수집"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests

from config.settings import get_settings

_BASE_URL = "https://www.alphavantage.co/query"


class NewsDataClient:
    """Alpha Vantage 뉴스 감성 분석 클라이언트"""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or get_settings().alpha_vantage_api_key

    def fetch_news_sentiment(
        self,
        tickers: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """종목/토픽 관련 뉴스 목록과 감성 점수를 반환한다.

        Args:
            tickers: 종목 티커 리스트 (예: ["AAPL", "MSFT"])
            topics: 토픽 리스트 (예: ["technology", "economy_macro"])
            limit: 반환할 뉴스 수 (최대 200)

        Returns:
            뉴스 기사 리스트 (title, summary, sentiment_score, sentiment_label 등)
        """
        params: Dict[str, str] = {
            "function": "NEWS_SENTIMENT",
            "apikey": self._api_key,
            "limit": str(min(limit, 200)),
            "sort": "RELEVANCE",
        }
        if tickers:
            params["tickers"] = ",".join(tickers)
        if topics:
            params["topics"] = ",".join(topics)

        resp = requests.get(_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        feed = data.get("feed", [])
        articles: List[Dict[str, Any]] = []

        for item in feed:
            ticker_sentiments = {}
            for ts in item.get("ticker_sentiment", []):
                ticker_sentiments[ts["ticker"]] = {
                    "relevance_score": float(ts.get("relevance_score", 0)),
                    "sentiment_score": float(ts.get("ticker_sentiment_score", 0)),
                    "sentiment_label": ts.get("ticker_sentiment_label", "Neutral"),
                }

            articles.append({
                "title": item.get("title", ""),
                "summary": item.get("summary", "")[:300],
                "source": item.get("source", ""),
                "published_at": item.get("time_published", ""),
                "overall_sentiment_score": float(
                    item.get("overall_sentiment_score", 0)
                ),
                "overall_sentiment_label": item.get(
                    "overall_sentiment_label", "Neutral"
                ),
                "ticker_sentiments": ticker_sentiments,
            })

        return articles

    def fetch_ticker_sentiment_summary(
        self, ticker: str, limit: int = 30
    ) -> Dict[str, Any]:
        """특정 종목에 대한 뉴스 감성 요약 통계를 반환한다."""
        articles = self.fetch_news_sentiment(tickers=[ticker], limit=limit)

        if not articles:
            return {
                "ticker": ticker,
                "article_count": 0,
                "avg_sentiment": 0.0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "overall_label": "Neutral",
            }

        scores = []
        bullish = bearish = neutral = 0

        for art in articles:
            ts = art["ticker_sentiments"].get(ticker)
            if ts:
                scores.append(ts["sentiment_score"])
                label = ts["sentiment_label"]
            else:
                scores.append(art["overall_sentiment_score"])
                label = art["overall_sentiment_label"]

            if "Bullish" in label:
                bullish += 1
            elif "Bearish" in label:
                bearish += 1
            else:
                neutral += 1

        avg = sum(scores) / len(scores) if scores else 0.0

        if avg >= 0.15:
            overall = "Bullish"
        elif avg <= -0.15:
            overall = "Bearish"
        else:
            overall = "Neutral"

        return {
            "ticker": ticker,
            "article_count": len(articles),
            "avg_sentiment": round(avg, 4),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "overall_label": overall,
        }
