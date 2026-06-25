"""일일 투자 보고서 생성 및 저장"""

from __future__ import annotations

import os
from datetime import date


_REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_store", "reports")


class ReportGenerator:
    """마크다운 형식의 일일 투자 보고서를 관리한다."""

    def __init__(self, report_dir: str = _REPORT_DIR):
        self._dir = report_dir
        os.makedirs(self._dir, exist_ok=True)

    def save_daily_report(self, content: str, report_date: date | None = None) -> str:
        """보고서를 파일로 저장하고 파일 경로를 반환한다."""
        d = report_date or date.today()
        filename = f"{d.isoformat()}_투자보고서.md"
        filepath = os.path.join(self._dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"  [Report] 저장 완료: {filepath}")
        return filepath

    def list_reports(self, limit: int = 30) -> list[dict]:
        """최근 보고서 목록을 반환한다."""
        files = sorted(
            [f for f in os.listdir(self._dir) if f.endswith(".md")],
            reverse=True,
        )[:limit]

        return [
            {"filename": f, "path": os.path.join(self._dir, f)}
            for f in files
        ]

    def read_report(self, filename: str) -> str | None:
        """보고서 파일 내용을 읽어 반환한다."""
        path = os.path.join(self._dir, filename)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
