"""카카오 refresh token 최초 발급 헬퍼 (로컬 1회 실행)

사전 준비 (Kakao Developers, https://developers.kakao.com):
  1) 애플리케이션 생성 → [앱 키]의 'REST API 키' 복사
  2) [카카오 로그인] 활성화 ON
  3) [카카오 로그인] → Redirect URI 등록 (예: https://localhost)
  4) [동의항목] → '카카오톡 메시지 전송(talk_message)' 사용 설정

실행:
    python -m notify.kakao_auth --rest-key <REST_API_KEY> --redirect https://localhost

흐름:
  - 출력된 인증 URL을 브라우저에서 열고 동의 → 리다이렉트된 주소창의 ?code=... 값 복사
  - 터미널에 code 붙여넣기 → refresh_token 출력
  - 이 refresh_token 을 KAKAO_REFRESH_TOKEN (GitHub Secret 등) 으로 저장
"""

from __future__ import annotations

import argparse

import requests

AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
TOKEN_URL = "https://kauth.kakao.com/oauth/token"


def main():
    ap = argparse.ArgumentParser(description="카카오 refresh token 발급")
    ap.add_argument("--rest-key", required=True, help="카카오 REST API 키")
    ap.add_argument("--redirect", default="https://localhost", help="등록된 Redirect URI")
    args = ap.parse_args()

    auth_url = (f"{AUTHORIZE_URL}?client_id={args.rest_key}"
                f"&redirect_uri={args.redirect}&response_type=code&scope=talk_message")
    print("\n[1] 아래 URL을 브라우저에서 열고 '동의'하세요:\n")
    print("    " + auth_url + "\n")
    print("[2] 동의 후 리다이렉트된 주소창에서 code= 뒤의 값을 복사하세요.")
    print("    (예: https://localhost/?code=ABCDEF... → 'ABCDEF...' 부분)\n")
    code = input("code 붙여넣기 > ").strip()

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": args.rest_key,
            "redirect_uri": args.redirect,
            "code": code,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"\n발급 실패 [{resp.status_code}]: {resp.text}")
        return
    data = resp.json()
    print("\n발급 성공! 아래 값을 안전하게 보관하세요.\n")
    print("  KAKAO_REFRESH_TOKEN =", data.get("refresh_token"))
    print("  (access_token 은 자동 갱신되므로 저장 불필요)")
    print("\n  refresh token 유효기간은 약 2개월이며, 메시지를 주기적으로 보내면 자동 연장됩니다.")


if __name__ == "__main__":
    main()
