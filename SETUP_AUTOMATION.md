# 매일 아침 10시 자동 리포트 — 설정 가이드

매일 **10:00 KST**에 시황 리포트를 생성해 **GitHub Pages**에 게시하고,
**이메일로 링크**를 전송합니다. PC를 켜둘 필요가 없습니다.

```
[GitHub Actions cron · 매일 01:00 UTC(=10:00 KST)]
   → daily_report.py 실행 (데이터 수집 + 재시도 + 완결성 검사)
   → _site/index.html 생성 → GitHub Pages 배포 (고정 URL)
   → notify.email_send 로 이메일에 "오늘 리포트 링크" 전송
```

> 💡 **일일 리포트는 별도 API 키가 필요 없습니다** (yfinance 등 공개 데이터만 사용).
> 등록할 비밀값은 **Gmail 발송 정보 2개뿐**입니다.
> (카카오톡 발송도 가능하지만 회사망에서 차단되는 경우가 있어 이메일을 권장합니다 — notify/kakao.py 참고)

---

## A. GitHub 저장소 만들기 & 푸시

이 프로젝트는 아직 git 저장소가 아닙니다. 로컬에서:

```bash
cd C:/cursor_p/stock
git init
git add .
git commit -m "시황 리포트 자동화"
```

GitHub에서 새 저장소(예: `stock-report`)를 만든 뒤:

```bash
git remote add origin https://github.com/<사용자명>/stock-report.git
git branch -M main
git push -u origin main
```

> `.env`, `_site/`, `status.json`, `reports/*.html` 은 `.gitignore`로 제외됩니다.
> (비밀키가 올라가지 않습니다.)

## B. GitHub Pages 활성화

저장소 → **Settings → Pages** →
**Build and deployment → Source = "GitHub Actions"** 선택.

배포되면 리포트 주소는 다음으로 고정됩니다(매일 같은 URL, 내용만 갱신):
```
https://<사용자명>.github.io/stock-report/
```

## C. Gmail '앱 비밀번호' 발급

GitHub Actions(클라우드)에서 Gmail SMTP로 메일을 보냅니다. 일반 비밀번호가 아닌
**앱 비밀번호(App Password)**가 필요합니다. (회사망 영향 없음 — 휴대폰에서도 설정 가능)

1. 구글 계정 **2단계 인증(2-Step Verification) 켜기**: https://myaccount.google.com/security
2. **앱 비밀번호 생성**: https://myaccount.google.com/apppasswords
   - 앱 이름(예: `stock-report`) 입력 → 생성 → **16자리 비밀번호**(공백 없이) 복사
   - ※ 2단계 인증이 꺼져 있으면 이 메뉴가 안 보입니다(1번 먼저).

## D. GitHub Secrets 등록

저장소 → **Settings → Secrets and variables → Actions → New repository secret**:

| 이름 | 값 |
|---|---|
| `SMTP_USER` | 보내는 Gmail 주소 (예: `coolboy30a@gmail.com`) |
| `SMTP_PASSWORD` | C-2에서 만든 16자리 앱 비밀번호 |
| `MAIL_TO` | (선택) 받는 주소. 미설정 시 `SMTP_USER`로 = 나에게 보냄 |

## E. 동작 확인

저장소 → **Actions → "일일 시황 리포트" → Run workflow** (수동 실행)로 즉시 테스트.
- 성공하면 Pages에 리포트가 뜨고 메일로 링크가 옵니다.
- 이후 매일 10시(KST)에 자동 실행됩니다.

로컬에서 테스트하려면:
```bash
# 생성만
python daily_report.py --out _site/index.html
# 이메일 발송 테스트 (환경변수 설정 후)
set SMTP_USER=coolboy30a@gmail.com
set SMTP_PASSWORD=<16자리 앱 비밀번호>
python -m notify.email_send --url "https://polabear30.github.io/stock-report/"
```

---

## 운영 메모

- **데이터 누락 방지**: 각 소스를 최대 3회 재시도하고, 실패해도 "조회 실패"로 표시하며
  리포트 하단 **"데이터 상태"** 줄(●/○)과 메일 제목·본문에 `⚠ 일부 데이터 누락`으로 알립니다.
  (말없이 넘어가지 않음)
- **UI 깨짐 방지**: 메일 본문에 리포트 HTML을 넣지 않고 **링크만** 보냅니다.
  링크는 실제 브라우저에서 열려 JS·차트·달력이 그대로 동작합니다.
- **cron 지연**: GitHub Actions 예약 실행은 부하에 따라 수 분~십수 분 지연될 수 있습니다(정상).
  또한 저장소가 60일간 활동이 없으면 예약이 비활성화되니, 가끔 커밋하거나 수동 실행하세요.
- **메일이 스팸함에 갈 수 있음**: 첫 메일이 스팸/프로모션함에 있으면 "스팸 아님" 처리하면
  이후 정상 수신됩니다. (보내는 주소 = 받는 주소가 같으면 보통 받은편지함으로 옵니다)
- **앱 비밀번호**: 구글 계정 비밀번호를 바꿔도 앱 비밀번호는 유지되지만, 계정 보안상
  취소되면 C 단계를 다시 수행해 새 앱 비밀번호로 `SMTP_PASSWORD`를 갱신하세요.
- **시간 변경**: `.github/workflows/daily-report.yml` 의 `cron: "0 1 * * *"` 수정
  (UTC 기준, 10시 KST = 1시 UTC).
- **공개 범위**: GitHub Pages는 공개 URL입니다. 공개 시장 데이터라 보통 무방하나,
  비공개가 필요하면 알려주세요(인증 호스팅으로 전환).
