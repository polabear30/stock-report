"""Cloud Run Job 엔트리포인트 — 일일 시황 리포트 생성·게시·발송

GitHub Actions를 대체한다. 한 번 실행되고 종료되는 배치(Job)다.

흐름:
    1) export_html.build_html()  로 리포트 HTML + 수집 상태(status) 생성
    2) Cloud Storage 공개 버킷에 index.html 업로드 (매일 같은 URL, 내용만 갱신)
    3) notify.email_send.send() 로 공개 URL을 이메일 전송

환경변수:
    GCS_BUCKET      — 업로드 대상 버킷명 (필수)
    GCS_OBJECT      — 오브젝트 경로 (기본 index.html)
    SMTP_USER       — 보내는 Gmail 주소 (없으면 이메일 단계 건너뜀)
    SMTP_PASSWORD   — Gmail 앱 비밀번호
    SMTP_HOST/PORT  — 기본 smtp.gmail.com / 587
    MAIL_TO         — 받는 주소 (미설정 시 SMTP_USER)

로컬 테스트:
    python run_job.py --no-upload --no-email   # 생성만 (로컬 파일로 저장)
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from export_html import build_html, KST


def upload_to_gcs(bucket_name: str, object_name: str, html: str) -> str:
    """HTML을 GCS 버킷에 업로드하고 공개 URL을 반환한다."""
    from google.cloud import storage  # 지연 import (로컬 생성 테스트 시 불필요)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    # 매일 갱신되는 리포트라 캐시를 짧게 — 항상 최신이 열리도록
    blob.cache_control = "no-cache, max-age=0"
    blob.upload_from_string(html, content_type="text/html; charset=utf-8")
    return f"https://storage.googleapis.com/{bucket_name}/{object_name}"


def main() -> int:
    ap = argparse.ArgumentParser(description="일일 시황 리포트 Job")
    ap.add_argument("--no-upload", action="store_true", help="GCS 업로드 생략(로컬 테스트)")
    ap.add_argument("--no-email", action="store_true", help="이메일 생략(로컬 테스트)")
    ap.add_argument("--out", default=None, help="로컬 HTML 저장 경로(선택)")
    args = ap.parse_args()

    print("[1/3] 데이터 수집·리포트 생성 중…")
    doc, status = build_html()
    failed = [k for k, v in status.items() if not v]
    print(f"      생성 완료 ({len(doc):,} bytes) · 상태: {status}")
    if failed:
        print(f"      ⚠ 수집 실패: {', '.join(failed)}")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"      로컬 저장: {args.out}")

    # 2) 업로드
    url = None
    if args.no_upload:
        print("[2/3] 업로드 생략(--no-upload)")
    else:
        bucket = os.environ.get("GCS_BUCKET")
        if not bucket:
            print("[2/3] ✗ GCS_BUCKET 환경변수가 없습니다.", file=sys.stderr)
            return 1
        obj = os.environ.get("GCS_OBJECT", "index.html")
        print(f"[2/3] GCS 업로드 중… gs://{bucket}/{obj}")
        url = upload_to_gcs(bucket, obj, doc)
        print(f"      게시 URL: {url}")

    # 3) 이메일
    if args.no_email:
        print("[3/3] 이메일 생략(--no-email)")
    elif not os.environ.get("SMTP_USER") or not os.environ.get("SMTP_PASSWORD"):
        print("[3/3] ⚠ SMTP 자격증명 없음 — 이메일 단계 건너뜀")
    elif not url:
        print("[3/3] ⚠ 게시 URL 없음(업로드 생략됨) — 이메일 단계 건너뜀")
    else:
        from notify.email_send import send
        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        print(f"[3/3] 이메일 발송 중… ({date_str})")
        send(url, None, date_str, status)

    print("완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
