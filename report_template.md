# 상위보고용 HTML 보고서 템플릿

> 이 파일은 Executive Briefing 스타일의 HTML 보고서 양식입니다.
> 새 보고서를 만들 때 이 템플릿을 기반으로 내용만 교체하여 사용하세요.

---

## 구성 요소 안내

| 구성 요소 | 용도 | 비고 |
|-----------|------|------|
| `.header` | 보고서 최상단 타이틀 영역 | 그라데이션 블루 배경 |
| `.section` + `.section-title` + `.num` | 번호가 매겨진 본문 섹션 | 카드 스타일 |
| `.callout` | 인용문 / 핵심 메시지 강조 | 좌측 색상 바 |
| `.key-metrics` + `.metric-card` | 주요 수치 카드 (그리드) | 자동 반응형 |
| `.comparison-table` + `.highlight-row` | 비교 테이블 | 블루 헤더 |
| `.leader-card` | 인물 소개 카드 | 아바타 + 설명 |
| `.insight-box` | 시사점 / 분석 박스 | 골드 배경 |
| `.timeline` + `.timeline-item` | 타임라인 (로드맵 등) | 세로 점선 |
| `.two-col` + `.mini-section` | 2단 비교 레이아웃 | 좌우 분할 |
| `.tag` | 인라인 태그/뱃지 | blue/green/orange/red |
| 하단 `.section` (그라데이션) | 핵심 요약 영역 | 블루 그라데이션 |
| `.footer` | 출처 및 작성일 | 하단 고정 |

---

## 전체 HTML 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{보고서 제목}}</title>
<style>
  :root {
    --primary: #1877F2;
    --primary-dark: #1464D8;
    --accent: #0668E1;
    --bg: #F7F8FA;
    --card: #FFFFFF;
    --text: #1C2B33;
    --text-secondary: #65676B;
    --border: #E4E6EB;
    --highlight: #E7F3FF;
    --success: #31A24C;
    --warning: #F7B928;
    --danger: #FA383E;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.7;
    padding: 40px 20px;
  }

  .container {
    max-width: 960px;
    margin: 0 auto;
  }

  .header {
    background: linear-gradient(135deg, #1877F2 0%, #0052CC 50%, #003D99 100%);
    color: white;
    padding: 48px 40px;
    border-radius: 16px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }

  .header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: rgba(255,255,255,0.05);
    border-radius: 50%;
  }

  .header .badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 16px;
    backdrop-filter: blur(4px);
  }

  .header h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }

  .header .subtitle {
    font-size: 16px;
    opacity: 0.9;
    font-weight: 400;
  }

  .header .meta-info {
    margin-top: 20px;
    display: flex;
    gap: 24px;
    font-size: 13px;
    opacity: 0.8;
  }

  .section {
    background: var(--card);
    border-radius: 12px;
    padding: 32px;
    margin-bottom: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }

  .section-title {
    font-size: 18px;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--highlight);
  }

  .section-title .num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: var(--primary);
    color: white;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 700;
    flex-shrink: 0;
  }

  .callout {
    background: var(--highlight);
    border-left: 4px solid var(--primary);
    padding: 16px 20px;
    border-radius: 0 8px 8px 0;
    margin: 16px 0;
    font-style: italic;
    color: #1a3a5c;
  }

  .callout .source {
    font-style: normal;
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 6px;
  }

  .key-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 20px 0;
  }

  .metric-card {
    background: linear-gradient(135deg, #f0f6ff, #e7f0ff);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid #d0e3ff;
  }

  .metric-card .value {
    font-size: 28px;
    font-weight: 800;
    color: var(--primary);
    letter-spacing: -1px;
  }

  .metric-card .label {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 4px;
    line-height: 1.4;
  }

  .timeline {
    position: relative;
    padding-left: 28px;
  }

  .timeline::before {
    content: '';
    position: absolute;
    left: 8px;
    top: 4px;
    bottom: 4px;
    width: 2px;
    background: var(--border);
  }

  .timeline-item {
    position: relative;
    margin-bottom: 20px;
    padding-left: 20px;
  }

  .timeline-item::before {
    content: '';
    position: absolute;
    left: -24px;
    top: 8px;
    width: 12px;
    height: 12px;
    background: var(--primary);
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 0 0 2px var(--primary);
  }

  .timeline-item .date {
    font-size: 12px;
    font-weight: 700;
    color: var(--primary);
    text-transform: uppercase;
  }

  .timeline-item .content {
    font-size: 14px;
    margin-top: 4px;
  }

  .comparison-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
    margin: 16px 0;
  }

  .comparison-table th {
    background: var(--primary);
    color: white;
    padding: 12px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 600;
  }

  .comparison-table td {
    padding: 12px 16px;
    font-size: 14px;
    border-bottom: 1px solid var(--border);
  }

  .comparison-table tr:last-child td { border-bottom: none; }
  .comparison-table tr:nth-child(even) td { background: #FAFBFC; }

  .highlight-row td {
    background: var(--highlight) !important;
    font-weight: 600;
  }

  .leader-card {
    display: flex;
    gap: 16px;
    padding: 16px;
    background: #FAFBFC;
    border-radius: 10px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
  }

  .leader-card .avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 18px;
    flex-shrink: 0;
  }

  .leader-card .info h4 {
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 2px;
  }

  .leader-card .info .role {
    font-size: 13px;
    color: var(--primary);
    font-weight: 600;
  }

  .leader-card .info .desc {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
  }

  .tag-blue { background: #E7F3FF; color: #0552B5; }
  .tag-green { background: #E6F4EA; color: #1B7A3D; }
  .tag-orange { background: #FFF4E5; color: #B86E00; }
  .tag-red { background: #FFE8E8; color: #C62828; }

  .insight-box {
    background: linear-gradient(135deg, #FFF8E1, #FFF3CD);
    border: 1px solid #FFE082;
    border-radius: 10px;
    padding: 20px;
    margin: 16px 0;
  }

  .insight-box .title {
    font-weight: 700;
    font-size: 14px;
    color: #B86E00;
    margin-bottom: 8px;
  }

  .insight-box ul {
    padding-left: 18px;
    font-size: 14px;
  }

  .insight-box li { margin-bottom: 6px; }

  ul.bullet-list {
    padding-left: 20px;
    font-size: 14px;
  }

  ul.bullet-list li {
    margin-bottom: 10px;
    line-height: 1.6;
  }

  ul.bullet-list li strong {
    color: var(--text);
  }

  .two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .mini-section {
    background: #FAFBFC;
    border-radius: 10px;
    padding: 20px;
    border: 1px solid var(--border);
  }

  .mini-section h4 {
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 12px;
    color: var(--text);
  }

  .info-box {
    background: #F0F6FF;
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 16px;
    border: 1px solid #D0E3FF;
  }

  .footer {
    text-align: center;
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 32px;
    padding: 20px;
  }

  @media (max-width: 700px) {
    .header { padding: 32px 24px; }
    .header h1 { font-size: 22px; }
    .section { padding: 24px; }
    .two-col { grid-template-columns: 1fr; }
    .key-metrics { grid-template-columns: 1fr 1fr; }
    .header .meta-info { flex-direction: column; gap: 6px; }
  }

  @media print {
    body { padding: 0; background: white; }
    .section { break-inside: avoid; box-shadow: none; }
  }
</style>
</head>
<body>

<div class="container">

  <!-- ==================== 헤더 ==================== -->
  <div class="header">
    <div class="badge">EXECUTIVE BRIEFING</div>
    <h1>{{보고서 제목}}</h1>
    <div class="subtitle">{{부제목 — 한 줄 요약}}</div>
    <div class="meta-info">
      <span>발표일: {{YYYY. M. DD (요일)}}</span>
      <span>출처: {{출처}}</span>
      <span>작성일: {{YYYY. M. DD}}</span>
    </div>
  </div>


  <!-- ==================== 섹션 (번호 + 제목) ==================== -->
  <div class="section">
    <div class="section-title">
      <span class="num">1</span>
      {{섹션 제목}}
    </div>

    <p style="font-size:15px; margin-bottom:16px;">
      {{본문 텍스트. <strong>굵은 글씨</strong>로 핵심 키워드를 강조할 수 있습니다.}}
    </p>

    <!-- 인용문 (블루) -->
    <div class="callout">
      "{{인용문 텍스트}}"
      <div class="source">— {{출처}}</div>
    </div>

    <!-- 인용문 (그린 변형) -->
    <div class="callout" style="border-left-color: #31A24C; background: #E6F4EA;">
      "{{인용문 텍스트}}"
      <div class="source">— {{출처}}</div>
    </div>

    <!-- 주요 수치 카드 (그리드) -->
    <div class="key-metrics">
      <div class="metric-card">
        <div class="value">{{수치}}</div>
        <div class="label">{{라벨 줄1}}<br>{{라벨 줄2}}</div>
      </div>
      <div class="metric-card">
        <div class="value">{{수치}}</div>
        <div class="label">{{라벨}}</div>
      </div>
      <div class="metric-card">
        <div class="value">{{수치}}</div>
        <div class="label">{{라벨}}</div>
      </div>
      <div class="metric-card">
        <div class="value">{{수치}}</div>
        <div class="label">{{라벨}}</div>
      </div>
    </div>
  </div>


  <!-- ==================== 불릿 리스트 섹션 ==================== -->
  <div class="section">
    <div class="section-title">
      <span class="num">2</span>
      {{섹션 제목}}
    </div>

    <h3 style="font-size:15px; font-weight:700; margin-bottom:12px;">{{소제목}}</h3>
    <ul class="bullet-list">
      <li><strong>{{항목 제목}}:</strong> {{항목 설명}}</li>
      <li><strong>{{항목 제목}}:</strong> {{항목 설명}}</li>
      <li><strong>{{항목 제목}}:</strong> {{항목 설명}}</li>
    </ul>

    <!-- 인사이트 박스 (골드) -->
    <div class="insight-box">
      <div class="title">{{인사이트 제목}}</div>
      <ul>
        <li>{{시사점 1}}</li>
        <li>{{시사점 2}}</li>
        <li>{{시사점 3}}</li>
      </ul>
    </div>
  </div>


  <!-- ==================== 비교 테이블 섹션 ==================== -->
  <div class="section">
    <div class="section-title">
      <span class="num">3</span>
      {{섹션 제목}}
    </div>

    <table class="comparison-table">
      <thead>
        <tr>
          <th>{{열 제목 1}}</th>
          <th>{{열 제목 2}}</th>
          <th>{{열 제목 3}}</th>
        </tr>
      </thead>
      <tbody>
        <tr class="highlight-row">
          <td><strong>{{강조 행}}</strong></td>
          <td>{{내용}} <span class="tag tag-blue">{{태그}}</span></td>
          <td>{{내용}}</td>
        </tr>
        <tr>
          <td>{{일반 행}}</td>
          <td>{{내용}}</td>
          <td>{{내용}}</td>
        </tr>
      </tbody>
    </table>
  </div>


  <!-- ==================== 인물 카드 섹션 ==================== -->
  <div class="section">
    <div class="section-title">
      <span class="num">4</span>
      {{섹션 제목}}
    </div>

    <div class="leader-card">
      <div class="avatar">{{이니셜}}</div>
      <div class="info">
        <h4>{{이름}}</h4>
        <div class="role">{{직책}}</div>
        <div class="desc">{{경력 및 설명}}</div>
      </div>
    </div>

    <!-- 정보 박스 (라이트 블루) -->
    <div class="info-box">
      <strong style="font-size:14px;">{{박스 제목}}</strong>
      <p style="font-size:14px; margin-top:6px;">{{박스 내용}}</p>
    </div>
  </div>


  <!-- ==================== 2단 비교 레이아웃 ==================== -->
  <div class="section">
    <div class="section-title">
      <span class="num">5</span>
      {{섹션 제목}}
    </div>

    <div class="two-col">
      <div class="mini-section">
        <h4>{{좌측 제목}}</h4>
        <ul class="bullet-list" style="font-size:13px;">
          <li><strong>{{항목}}:</strong> {{설명}}</li>
          <li><strong>{{항목}}:</strong> {{설명}}</li>
        </ul>
      </div>
      <div class="mini-section">
        <h4>{{우측 제목}}</h4>
        <ul class="bullet-list" style="font-size:13px;">
          <li><strong>{{항목}}:</strong> {{설명}}</li>
          <li><strong>{{항목}}:</strong> {{설명}}</li>
        </ul>
      </div>
    </div>
  </div>


  <!-- ==================== 타임라인 섹션 ==================== -->
  <div class="section">
    <div class="section-title">
      <span class="num">6</span>
      {{섹션 제목}}
    </div>

    <div class="timeline">
      <div class="timeline-item">
        <div class="date">{{날짜}}</div>
        <div class="content">{{내용}}</div>
      </div>
      <div class="timeline-item">
        <div class="date">{{날짜}}</div>
        <div class="content">{{내용}}</div>
      </div>
      <div class="timeline-item">
        <div class="date">{{날짜}}</div>
        <div class="content">{{내용}}</div>
      </div>
    </div>
  </div>


  <!-- ==================== 핵심 요약 (블루 그라데이션) ==================== -->
  <div class="section" style="background: linear-gradient(135deg, #1877F2, #0052CC); color: white; text-align: center;">
    <div class="section-title" style="color: white; border-bottom-color: rgba(255,255,255,0.2); justify-content: center;">
      핵심 한 줄 요약
    </div>
    <p style="font-size: 17px; font-weight: 600; line-height: 1.8; max-width: 700px; margin: 0 auto;">
      {{핵심 요약 텍스트}}
    </p>
  </div>


  <!-- ==================== 출처 ==================== -->
  <div class="section" style="padding: 24px 32px;">
    <div class="section-title" style="font-size: 15px; margin-bottom: 12px;">
      참고 출처
    </div>
    <ul style="font-size: 12px; color: var(--text-secondary); padding-left: 18px; line-height: 1.9;">
      <li>{{매체명}} — "{{기사 제목}}" ({{날짜}})</li>
      <li>{{매체명}} — "{{기사 제목}}" ({{날짜}})</li>
    </ul>
  </div>

  <div class="footer">
    {{하단 안내 텍스트}} | {{작성일}}
  </div>

</div>

</body>
</html>
```

---

## 사용 가능한 태그(뱃지) 색상

```html
<span class="tag tag-blue">블루 태그</span>
<span class="tag tag-green">그린 태그</span>
<span class="tag tag-orange">오렌지 태그</span>
<span class="tag tag-red">레드 태그</span>
```

## 인용문(Callout) 색상 변형

```html
<!-- 기본 (블루) -->
<div class="callout">인용문</div>

<!-- 그린 변형 -->
<div class="callout" style="border-left-color: #31A24C; background: #E6F4EA;">인용문</div>

<!-- 레드 변형 -->
<div class="callout" style="border-left-color: #FA383E; background: #FFE8E8;">경고/주의</div>

<!-- 오렌지 변형 -->
<div class="callout" style="border-left-color: #F7B928; background: #FFF4E5;">참고사항</div>
```

## 테마 색상 커스터마이징

`:root` 변수를 수정하면 전체 색상 테마를 변경할 수 있습니다.

```css
:root {
  --primary: #1877F2;     /* 메인 색상 (헤더, 번호, 링크 등) */
  --primary-dark: #1464D8; /* 메인 색상 어두운 변형 */
  --accent: #0668E1;       /* 강조 색상 */
  --bg: #F7F8FA;           /* 페이지 배경 */
  --card: #FFFFFF;         /* 카드 배경 */
  --text: #1C2B33;         /* 본문 텍스트 */
  --text-secondary: #65676B; /* 보조 텍스트 */
  --border: #E4E6EB;       /* 테두리 */
  --highlight: #E7F3FF;    /* 하이라이트 배경 */
}
```
