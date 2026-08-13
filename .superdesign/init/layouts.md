# Layouts

## App Shell

- Source: `front/index.html`
- Description: Single-page local MVP with app header, two tab panels, chat input screen, and analysis result screen.

```html
<main class="app-shell">
  <header class="app-header">
    <p class="eyebrow">SilentGuard Demo</p>
    <h1>사이버 따돌림 검증 프로그램</h1>
    <p class="app-description">채팅 입력부터 위험 신호 분석, 관리자용 사건 알림까지 한 흐름으로 확인하는 로컬 MVP입니다.</p>
  </header>

  <nav class="screen-tabs" aria-label="화면 전환">
    <button type="button" id="chat-screen-btn" class="screen-tab is-active">1. 채팅방 화면</button>
    <button type="button" id="result-screen-btn" class="screen-tab">2. 분석 결과 화면</button>
  </nav>
</main>
```

## Result Layout

- Source: `front/index.html`
- Description: Analysis page uses a metric grid followed by two detail columns for risk segments and incident notification.

```html
<section id="result-screen" class="screen-panel">
  <section id="analysis-result" class="panel analysis-overview-panel">
    <div class="result-grid result-grid-three">
      <div id="risk-result-card" class="result-card"></div>
      <div id="risk-level-card" class="result-card"></div>
      <div class="result-card notification-summary-card"></div>
    </div>
  </section>

  <div class="result-detail-grid">
    <section id="risk-segments" class="panel result-detail-panel"></section>
    <section id="agent-alert" class="panel result-detail-panel"></section>
  </div>
</section>
```
