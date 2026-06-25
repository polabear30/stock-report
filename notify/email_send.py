"""이메일로 리포트 링크 전송 (SMTP)

본문에는 리포트 HTML을 넣지 않고 '링크'만 보낸다(메일 용량 제한·UI 깨짐 방지).
링크는 실제 브라우저에서 열려 차트·달력이 그대로 동작한다.

환경변수:
    SMTP_USER       — 보내는 Gmail 주소 (예: coolboy30a@gmail.com)
    SMTP_PASSWORD   — Gmail '앱 비밀번호' 16자리 (계정 비밀번호 아님)
    SMTP_HOST       — 기본 smtp.gmail.com
    SMTP_PORT       — 기본 587
    MAIL_TO         — 받는 주소(미설정 시 SMTP_USER 와 동일, 즉 나에게)

CLI:
    python -m notify.email_send --url <리포트URL> [--to a@b.com] [--status-file status.json]
"""

from __future__ import annotations

import argparse
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

CRITICAL = ("지수·금리", "공포탐욕", "풋/콜")


def _warn(status: Optional[dict]) -> str:
    if not status:
        return ""
    failed = [k for k, v in status.items() if not v]
    if not failed:
        return ""
    crit = [k for k in CRITICAL if not status.get(k, True)]
    tag = "⚠ 일부 핵심 데이터 누락" if crit else "※ 보조 데이터 일부 누락"
    return f"{tag}: {', '.join(failed)}"


def _html(url: str, date_str: str, warn: str) -> str:
    warn_html = (f'<p style="margin:0 0 14px;color:#B45309;font-size:13px;">{warn}</p>'
                 if warn else "")
    return f"""<!DOCTYPE html><html><body style="margin:0;padding:24px;background:#F3F4F6;font-family:Arial,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
    <table role="presentation" width="100%" style="max-width:480px;background:#fff;border-radius:12px;padding:28px 26px;">
      <tr><td>
        <p style="margin:0 0 4px;font-size:13px;color:#6B7280;">US Market Briefing</p>
        <h1 style="margin:0 0 6px;font-size:20px;color:#111827;">📊 미국 증시 시황 브리핑</h1>
        <p style="margin:0 0 18px;font-size:14px;color:#6B7280;">{date_str}</p>
        {warn_html}
        <p style="margin:0 0 22px;font-size:14px;color:#374151;line-height:1.6;">
          오늘의 주요 지수·금리·원자재, 공포탐욕지수, 풋/콜 비율, 경제 캘린더를
          아래 버튼에서 확인하세요.</p>
        <table role="presentation" cellpadding="0" cellspacing="0"><tr>
          <td style="border-radius:8px;background:#2563EB;">
            <a href="{url}" style="display:inline-block;padding:13px 26px;font-size:15px;font-weight:bold;color:#fff;text-decoration:none;">리포트 열기 →</a>
          </td>
        </tr></table>
        <p style="margin:18px 0 0;font-size:12px;color:#9CA3AF;word-break:break-all;">{url}</p>
        <hr style="border:none;border-top:1px solid #E5E7EB;margin:22px 0 12px;">
        <p style="margin:0;font-size:11px;color:#9CA3AF;">US Stock AI Agent · 매일 오전 자동 발송 · 데이터 스냅샷</p>
      </td></tr>
    </table>
  </td></tr></table>
</body></html>"""


def send(url: str, to: Optional[str], date_str: str, status: Optional[dict] = None) -> bool:
    user = os.environ.get("SMTP_USER")
    pw = os.environ.get("SMTP_PASSWORD")
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    to = to or os.environ.get("MAIL_TO") or user
    if not user or not pw:
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD 환경변수가 없습니다.")

    warn = _warn(status)
    subject = f"📊 미국 증시 시황 브리핑 ({date_str})" + (f" {warn.split(':')[0]}" if warn else "")
    plain = f"미국 증시 시황 브리핑 ({date_str})\n{warn + chr(10) if warn else ''}리포트: {url}"

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("미국증시 시황봇", user))
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(_html(url, date_str, warn), "html", "utf-8"))

    with smtplib.SMTP(host, port, timeout=20) as s:
        s.ehlo()
        s.starttls()
        s.login(user, pw)
        s.sendmail(user, [a.strip() for a in to.split(",")], msg.as_string())
    print(f"  [Email] 발송 완료 → {to}")
    return True


def main():
    ap = argparse.ArgumentParser(description="리포트 링크 이메일 전송")
    ap.add_argument("--url", required=True)
    ap.add_argument("--to", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--status-file", default=None)
    args = ap.parse_args()

    if args.date:
        date_str = args.date
    else:
        from datetime import datetime, timezone, timedelta
        date_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")

    status = None
    if args.status_file and os.path.exists(args.status_file):
        with open(args.status_file, encoding="utf-8") as f:
            status = json.load(f)

    send(args.url, args.to, date_str, status)


if __name__ == "__main__":
    main()
