"""카카오톡 '나에게 보내기' (메모 API) 발송 모듈

Kakao Developers 앱의 REST API 키 + refresh token으로 access token을 갱신한 뒤,
'나에게 보내기' 기본 텍스트 템플릿으로 링크가 포함된 메시지를 전송한다.

환경변수:
    KAKAO_REST_API_KEY   — 카카오 앱 REST API 키
    KAKAO_REFRESH_TOKEN  — talk_message 동의로 발급받은 refresh token
                           (최초 1회 notify/kakao_auth.py 로 발급)

CLI:
    python -m notify.kakao --url <리포트URL> [--status-file status.json] [--date 2026-06-25]
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Optional

import requests

TOKEN_URL = "https://kauth.kakao.com/oauth/token"
MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


class KakaoError(RuntimeError):
    pass


def refresh_access_token(rest_api_key: str, refresh_token: str) -> dict:
    """refresh token으로 새 access token을 발급받는다."""
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": rest_api_key,
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        raise KakaoError(f"토큰 갱신 실패 [{resp.status_code}]: {resp.text}")
    return resp.json()


def send_to_me(text: str, link_url: str, button_title: str = "리포트 열기",
               rest_api_key: Optional[str] = None,
               refresh_token: Optional[str] = None) -> bool:
    """'나에게 보내기'로 링크가 포함된 텍스트 메시지를 전송한다."""
    rest_api_key = rest_api_key or os.environ.get("KAKAO_REST_API_KEY")
    refresh_token = refresh_token or os.environ.get("KAKAO_REFRESH_TOKEN")
    if not rest_api_key or not refresh_token:
        raise KakaoError("KAKAO_REST_API_KEY / KAKAO_REFRESH_TOKEN 환경변수가 없습니다.")

    tok = refresh_access_token(rest_api_key, refresh_token)
    access_token = tok.get("access_token")
    if not access_token:
        raise KakaoError(f"access_token 없음: {tok}")

    # 카카오는 refresh token 만료 1개월 전부터 새 토큰을 함께 내려준다.
    # 저장된 값을 갱신하지 않으면 ~2개월 후 만료되므로, 새 토큰이 오면 반드시 알린다.
    new_refresh = tok.get("refresh_token")
    if new_refresh and new_refresh != refresh_token:
        print("  [Kakao][중요] 새 refresh token이 발급되었습니다. "
              "KAKAO_REFRESH_TOKEN 시크릿을 아래 값으로 갱신하세요:")
        print("  " + new_refresh)

    # 카카오 텍스트 메시지는 200자 제한 → 안전하게 자른다
    text = text[:190]
    template = {
        "object_type": "text",
        "text": text,
        "link": {"web_url": link_url, "mobile_web_url": link_url},
        "button_title": button_title,
    }
    resp = requests.post(
        MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=10,
    )
    if resp.status_code != 200:
        raise KakaoError(f"메시지 전송 실패 [{resp.status_code}]: {resp.text}")
    print("  [Kakao] '나에게 보내기' 전송 완료")
    return True


def _compose(date_str: str, status: Optional[dict]) -> str:
    critical = ("지수·금리", "공포탐욕", "풋/콜")
    warn = ""
    if status:
        failed_crit = [k for k in critical if not status.get(k, True)]
        failed_all = [k for k, v in status.items() if not v]
        if failed_crit:
            warn = f"\n⚠ 일부 핵심 데이터 누락: {', '.join(failed_all)}"
        elif failed_all:
            warn = f"\n※ 보조 데이터 일부 누락: {', '.join(failed_all)}"
    return (f"📊 미국 증시 시황 브리핑 ({date_str})\n"
            f"지수·공포탐욕·풋콜·경제캘린더를 링크에서 확인하세요.{warn}")


def main():
    ap = argparse.ArgumentParser(description="카카오톡 나에게 보내기")
    ap.add_argument("--url", required=True, help="리포트 URL")
    ap.add_argument("--date", default=None, help="표시할 날짜 (기본: 오늘 KST)")
    ap.add_argument("--status-file", default=None, help="수집 상태 JSON 경로")
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

    send_to_me(_compose(date_str, status), args.url)


if __name__ == "__main__":
    main()
