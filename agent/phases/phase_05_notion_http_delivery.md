# Phase 05: Notion HTTP API 보고서 생성

## 목표

Agent 분석 결과와 원본 메시지를 실제 Notion 페이지로 만들고 생성된 URL을 반환한다.

## 참고 문서

- 팀 공통 `AGENTS.md`
- `agent/AGENTS.md`
- `agent/overview.md`
- `agent/PHASE_DOCUMENT_RULES.md`
- Notion API Create a page 공식 문서

## 해야 할 일

- [x] `.env.example`에 Notion API 설정값을 추가한다.
- [x] Notion 페이지 제목과 본문을 분리해서 만들 수 있게 한다.
- [x] Notion HTTP API 요청 body와 headers를 만드는 함수를 작성한다.
- [x] Notion API 응답에서 page URL을 반환하는 함수를 작성한다.
- [x] Phase 5 실행 파일을 만든다.
- [x] 테스트로 요청 body, 설정값, URL 반환을 확인한다.
- [ ] 실제 로컬 Python 명령으로 Notion HTTP API 생성까지 확인한다.

## 입력과 출력

입력:

```text
ai/legacy_app/sample_input.json
ai/legacy_app/sample_incident_result.json
.env의 NOTION_TOKEN
.env의 NOTION_PARENT_PAGE_ID
```

출력:

```json
{
  "ok": true,
  "title": "SilentGuard 위험 신호 알림 - incident_demo_001",
  "notion_url": "https://www.notion.so/...",
  "notion_page_id": "page_001"
}
```

## 변경 파일

- `.env.example`
- `ai/notification/notion_markdown.py`
- `ai/notification/notion_delivery.py`
- `ai/legacy_app/run_phase_05.py`
- `ai/legacy_app/test_notion_delivery.py`
- `agent/phases/phase_05_notion_http_delivery.md`
- `agent/phases/phase_05_status.md`

## 검증 방법

```bash
python3 -m pytest test -q
```

## 작업 결과

Notion HTTP API로 페이지를 생성하고 URL을 반환하는 코드 경로를 만들었다.

현재 전체 테스트 17개가 통과했다.

Notion HTTP API로 관리자별 사건 정리 부모 페이지 아래에 실제 하위 사건 페이지 생성을 확인했다.

생성된 확인용 사건 페이지:

```text
https://app.notion.com/p/SilentGuard-incident_demo_001-3b9590c0a92681ba824ad2a3676bcd43
```

## 남은 문제

없음

## 다음 Phase로 넘길 내용

이메일 알림은 Phase 5의 `notion_url`과 채팅방 생성 시 받은 `notification_email`을 사용해 짧은 링크 알림으로 보내면 된다. 현재 MVP에서는 실제 이메일 발송은 미구현이고, 백엔드는 `notification_delivery.recipient_email`로 수신 대상을 반환한다.
