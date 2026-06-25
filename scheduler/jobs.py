"""APScheduler 기반 예약 작업 정의"""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config.settings import get_settings


def daily_analysis_job():
    """매일 장 마감 후 전체 분석 파이프라인을 실행한다."""
    print("\n" + "=" * 60)
    print("  [Scheduler] 일일 분석 시작")
    print("=" * 60)

    from agent.engine import StockAgent
    from portfolio.manager import PortfolioManager

    try:
        agent = StockAgent()
        result = agent.run()

        pm = PortfolioManager()
        pm.take_snapshot()

        print("\n  [Scheduler] 일일 분석 완료")
        print(f"  [Scheduler] 결과 길이: {len(result)} chars")
    except Exception as e:
        print(f"\n  [Scheduler] 분석 실패: {e}")
        _send_error_alert(str(e))


def hourly_alert_job():
    """매시간 관심 종목 가격 변동을 체크하고 이상 시 알림을 발송한다."""
    print("\n  [Scheduler] 가격 변동 체크 시작")

    from data.market import MarketDataClient
    from alerts.email import EmailAlertSender

    settings = get_settings()
    CHANGE_THRESHOLD = 5.0

    try:
        market = MarketDataClient()
        sender = EmailAlertSender()

        for ticker in settings.watchlist_tickers:
            try:
                snap = market.get_snapshot(ticker)
                change = abs(snap.get("change_pct", 0))

                if change >= CHANGE_THRESHOLD:
                    direction = "급등" if snap["change_pct"] > 0 else "급락"
                    sender.send(
                        subject=f"{ticker} {direction} 알림 ({snap['change_pct']:+.1f}%)",
                        body=(
                            f"## {ticker} {direction} 감지\n\n"
                            f"- 현재가: ${snap['price']:.2f}\n"
                            f"- 전일 대비: {snap['change_pct']:+.2f}%\n"
                            f"- 거래량: {snap.get('volume', 'N/A'):,}\n"
                        ),
                        priority="high",
                    )
            except Exception as e:
                print(f"  [Alert] {ticker} 조회 실패: {e}")

    except Exception as e:
        print(f"  [Scheduler] 알림 체크 실패: {e}")


def _send_error_alert(error_msg: str):
    """에러 발생 시 관리자에게 알림"""
    try:
        from alerts.email import EmailAlertSender
        sender = EmailAlertSender()
        sender.send(
            subject="Agent Error Alert",
            body=f"## Agent 실행 오류\n\n```\n{error_msg}\n```",
            priority="high",
        )
    except Exception:
        pass


def create_scheduler() -> BlockingScheduler:
    """스케줄러를 생성하고 작업을 등록한다."""
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.timezone)

    scheduler.add_job(
        daily_analysis_job,
        trigger=CronTrigger(
            hour=settings.analysis_hour,
            minute=settings.analysis_minute,
            timezone=settings.timezone,
        ),
        id="daily_analysis",
        name="Daily Stock Analysis",
        replace_existing=True,
    )

    scheduler.add_job(
        hourly_alert_job,
        trigger=CronTrigger(minute=0, timezone=settings.timezone),
        id="hourly_alert",
        name="Hourly Price Alert",
        replace_existing=True,
    )

    return scheduler
