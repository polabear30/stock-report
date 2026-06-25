"""환경변수 기반 설정 관리 (Pydantic Settings)"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Claude
    anthropic_api_key: str = ""

    # Polygon.io
    polygon_api_key: str = ""

    # FRED
    fred_api_key: str = ""

    # Alpha Vantage
    alpha_vantage_api_key: str = ""

    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    alert_recipients: str = ""

    # Portfolio
    watchlist: str = "AAPL,MSFT,GOOGL,AMZN,NVDA,TSLA,QQQ,SPY"
    initial_cash: float = 100_000.0

    # Scheduler
    analysis_hour: int = 16
    analysis_minute: int = 30
    timezone: str = "US/Eastern"

    @property
    def watchlist_tickers(self) -> List[str]:
        return [t.strip() for t in self.watchlist.split(",") if t.strip()]

    @property
    def recipient_list(self) -> List[str]:
        return [r.strip() for r in self.alert_recipients.split(",") if r.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
