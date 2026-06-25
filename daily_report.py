"""일일 시황 리포트 생성 (GitHub Actions / 로컬 공용)

HTML 리포트와 수집 상태(status.json)를 생성한다. 카톡 전송은 별도 단계
(notify.kakao)에서 실제 게시 URL로 수행한다.

사용법:
    python daily_report.py --out _site/index.html --status-out status.json
    python daily_report.py --notify-url https://example.com   # 로컬에서 즉시 카톡까지
"""

from __future__ import annotations

import argparse
import json
import os

from export_html import build_html, KST


def main():
    ap = argparse.ArgumentParser(description="일일 시황 리포트 생성")
    ap.add_argument("--out", default="_site/index.html", help="HTML 출력 경로")
    ap.add_argument("--status-out", default="status.json", help="수집 상태 JSON 경로")
    ap.add_argument("--notify-url", default=None,
                    help="지정 시 생성 후 카톡 '나에게 보내기' (로컬 테스트용)")
    args = ap.parse_args()

    print("데이터 수집 중…")
    doc, status = build_html()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(doc)
    with open(args.status_out, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False)

    failed = [k for k, v in status.items() if not v]
    print(f"생성 완료: {args.out} ({os.path.getsize(args.out):,} bytes)")
    print(f"  상태: {status}")
    if failed:
        print(f"  ⚠ 수집 실패: {', '.join(failed)}")

    if args.notify_url:
        from datetime import datetime
        from notify.kakao import send_to_me, _compose
        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        send_to_me(_compose(date_str, status), args.notify_url)


if __name__ == "__main__":
    main()
