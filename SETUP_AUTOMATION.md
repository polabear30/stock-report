# 매일 아침 10시 자동 리포트 — 설정 가이드

매일 **10:00 KST**에 시황 리포트를 생성해 **GitHub Pages**에 게시하고,
**카카오톡 '나에게 보내기'**로 링크를 전송합니다. PC를 켜둘 필요가 없습니다.

```
[GitHub Actions cron · 매일 01:00 UTC(=10:00 KST)]
   → daily_report.py 실행 (데이터 수집 + 재시도 + 완결성 검사)
   → _site/index.html 생성 → GitHub Pages 배포 (고정 URL)
   → notify.kakao 로 카톡에 "오늘 리포트 링크" 전송
```

> 💡 **일일 리포트는 별도 API 키가 필요 없습니다** (yfinance 등 공개 데이터만 사용).
> 등록할 비밀값은 **카카오 2개뿐**입니다.

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

## C. 카카오 앱 만들기 & refresh token 발급

1. https://developers.kakao.com → **내 애플리케이션 → 애플리케이션 추가하기**
2. **앱 키 → REST API 키** 복사
3. **카카오 로그인 → 활성화 설정 ON**
4. **카카오 로그인 → Redirect URI 등록**: `https://localhost`
5. **카카오 로그인 → 동의항목 → 카카오톡 메시지 전송(`talk_message`)** 사용 설정
6. 로컬에서 refresh token 발급:

```bash
python -m notify.kakao_auth --rest-key <REST_API_KEY> --redirect https://localhost
```
   - 출력된 URL을 브라우저에서 열고 **동의**
   - 리다이렉트된 주소 `https://localhost/?code=XXXX` 에서 `XXXX` 복사 → 터미널에 붙여넣기
   - 출력된 **`KAKAO_REFRESH_TOKEN`** 값 복사

## D. GitHub Secrets 등록

저장소 → **Settings → Secrets and variables → Actions → New repository secret**:

| 이름 | 값 |
|---|---|
| `KAKAO_REST_API_KEY` | C-2에서 복사한 REST API 키 |
| `KAKAO_REFRESH_TOKEN` | C-6에서 발급받은 refresh token |

## E. 동작 확인

저장소 → **Actions → "일일 시황 리포트" → Run workflow** (수동 실행)로 즉시 테스트.
- 성공하면 Pages에 리포트가 뜨고 카톡으로 링크가 옵니다.
- 이후 매일 10시(KST)에 자동 실행됩니다.

로컬에서 한 번에 테스트하려면:
```bash
# 생성만
python daily_report.py --out _site/index.html
# 생성 + 카톡까지 (환경변수 설정 후)
set KAKAO_REST_API_KEY=...
set KAKAO_REFRESH_TOKEN=...
python daily_report.py --notify-url "https://<사용자명>.github.io/stock-report/"
```

---

## 운영 메모

- **데이터 누락 방지**: 각 소스를 최대 3회 재시도하고, 실패해도 "조회 실패"로 표시하며
  리포트 하단 **"데이터 상태"** 줄(●/○)과 카톡 메시지에 `⚠ 일부 데이터 누락`으로 알립니다.
  (말없이 넘어가지 않음)
- **UI 깨짐 방지**: 메일/메신저 본문에 HTML을 넣지 않고 **링크만** 보냅니다.
  링크는 실제 브라우저에서 열려 JS·차트·달력이 그대로 동작합니다.
- **cron 지연**: GitHub Actions 예약 실행은 부하에 따라 수 분~십수 분 지연될 수 있습니다(정상).
  또한 저장소가 60일간 활동이 없으면 예약이 비활성화되니, 가끔 커밋하거나 수동 실행하세요.
- **refresh token 만료(~2개월)**: 매일 사용하면 자동 연장되지만, 만료 1개월 전 카카오가
  **새 토큰**을 내려줍니다. 그때 Actions 로그에 `[Kakao][중요] 새 refresh token...` 이 찍히면
  그 값으로 `KAKAO_REFRESH_TOKEN` 시크릿을 갱신하세요. (또는 만료 시 C-6 재실행)
- **시간 변경**: `.github/workflows/daily-report.yml` 의 `cron: "0 1 * * *"` 수정
  (UTC 기준, 10시 KST = 1시 UTC).
- **공개 범위**: GitHub Pages는 공개 URL입니다. 공개 시장 데이터라 보통 무방하나,
  비공개가 필요하면 알려주세요(인증 호스팅으로 전환).
