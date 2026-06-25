"""SMTP 기반 이메일 알림 발송"""

from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config.settings import get_settings


class EmailAlertSender:
    """이메일 알림 발송 클라이언트"""

    PRIORITY_HEADERS = {
        "high": "1 (Highest)",
        "normal": "3 (Normal)",
        "low": "5 (Lowest)",
    }

    def __init__(self, settings=None):
        self._s = settings or get_settings()

    def send(
        self,
        subject: str,
        body: str,
        priority: str = "normal",
        recipients: Optional[list] = None,
    ) -> bool:
        """이메일을 발송하고 성공 여부를 반환한다."""
        to_list = recipients or self._s.recipient_list
        if not to_list:
            print("  [Email] 수신자가 설정되지 않았습니다.")
            return False

        if not self._s.smtp_user or not self._s.smtp_password:
            print("  [Email] SMTP 인증 정보가 없습니다. 알림을 건너뜁니다.")
            self._log_locally(subject, body)
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self._s.smtp_user
        msg["To"] = ", ".join(to_list)
        msg["Subject"] = f"[Stock Agent] {subject}"
        msg["X-Priority"] = self.PRIORITY_HEADERS.get(priority, "3 (Normal)")

        html = self._markdown_to_html(body)
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            with smtplib.SMTP(self._s.smtp_host, self._s.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self._s.smtp_user, self._s.smtp_password)
                server.sendmail(self._s.smtp_user, to_list, msg.as_string())
            print(f"  [Email] 발송 완료: {subject}")
            return True
        except Exception as e:
            print(f"  [Email] 발송 실패: {e}")
            self._log_locally(subject, body)
            return False

    @staticmethod
    def _markdown_to_html(md_text: str) -> str:
        """간단한 마크다운 → HTML 변환 (제목, 볼드, 줄바꿈)"""
        lines = md_text.split("\n")
        html_lines = []
        for line in lines:
            if line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.strip() == "":
                html_lines.append("<br>")
            else:
                html_lines.append(f"<p>{line}</p>")
        return f"<html><body style='font-family: sans-serif;'>{''.join(html_lines)}</body></html>"

    @staticmethod
    def _log_locally(subject: str, body: str):
        print(f"  [Email 로컬 로그] 제목: {subject}")
        print(f"  [Email 로컬 로그] 내용: {body[:200]}...")
