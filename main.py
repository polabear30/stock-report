"""미국 주식 AI 에이전트 — 메인 진입점

사용법:
    # 스케줄러 모드 (자동 실행)
    python main.py

    # 즉시 분석 모드 (한 번 실행)
    python main.py --run-now

    # 대시보드 실행
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import argparse
import sys


def run_scheduler():
    """스케줄러를 시작하여 예약된 시간에 자동 분석을 실행한다."""
    from config.settings import get_settings
    from scheduler.jobs import create_scheduler

    settings = get_settings()
    print()
    print("=" * 60)
    print("  US Stock AI Agent — Scheduler Mode")
    print("=" * 60)
    print()
    print(f"  Analysis schedule: {settings.analysis_hour:02d}:{settings.analysis_minute:02d} {settings.timezone}")
    print(f"  Watchlist: {', '.join(settings.watchlist_tickers)}")
    print(f"  Alert check: Every hour")
    print()
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    scheduler = create_scheduler()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n  [Scheduler] 종료합니다.")


def run_now():
    """즉시 전체 분석 파이프라인을 실행한다."""
    from agent.engine import StockAgent
    from portfolio.manager import PortfolioManager
    from config.settings import get_settings

    settings = get_settings()
    print()
    print("=" * 60)
    print("  US Stock AI Agent — Immediate Run")
    print("=" * 60)
    print(f"  Watchlist: {', '.join(settings.watchlist_tickers)}")
    print()

    agent = StockAgent()
    result = agent.run()

    pm = PortfolioManager()
    pm.take_snapshot()

    print()
    print("=" * 60)
    print("  [ Analysis Result ]")
    print("=" * 60)
    print()
    print(result)
    print()
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="US Stock AI Agent")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run analysis immediately instead of starting the scheduler",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Custom prompt for the agent (use with --run-now)",
    )
    args = parser.parse_args()

    if args.run_now:
        if args.prompt:
            from agent.engine import StockAgent
            agent = StockAgent()
            result = agent.run(user_prompt=args.prompt)
            print(result)
        else:
            run_now()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
