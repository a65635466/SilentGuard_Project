# Phase 08: 백엔드 -> 이메일 알림

## 전달 방향

```text
백엔드 -> Notion 보고서 생성 -> SMTP 이메일 전송 -> 프론트엔드 알림 전달 상태
```

## 목표

`warning` 이상에서 Agent 분석과 근거 메시지 ID 검증이 통과하면 백엔드는 Notion 보고서를 만든 뒤, 생성된 Notion 링크를 채팅방 생성 시 입력받은 `notification_email`로 전송한다.

프론트엔드의 `알림 전달 상태`는 Notion 문서 생성 상태가 아니라 이메일 전송 상태를 표시한다.

## 환경 변수

```text
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_USE_TLS=
EMAIL_FROM_NAME=
```

## 이메일 입력 데이터

```json
{
  "analysis_id": "analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6",
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "messages": [],
  "bullying_probability": 0.91,
  "risk_level": "immediate",
  "incident": {
    "incident_id": "incident_room_20260812143005_a1b2c3_001",
    "manager_summary": "관리자 확인이 필요합니다."
  }
}
```

Notion 생성 결과:

```json
{
  "notion_url": "https://app.notion.com/p/...",
  "notion_page_id": "notion_page_id"
}
```

## 이메일 전달 결과

```json
{
  "channel": "email",
  "status": "sent",
  "sent_at": "2026-08-12T14:30:05+09:00",
  "external_message_id": "smtp-message-id",
  "notion_url": "https://app.notion.com/p/...",
  "notion_page_id": "notion_page_id",
  "recipient_email": "teacher@example.com"
}
```

## 상태 기준

| status | 의미 |
| --- | --- |
| `sent` | Notion 링크 이메일 전송 성공 |
| `email_not_configured` | SMTP 환경변수 누락 |
| `email_failed` | SMTP 연결, 인증 또는 발송 실패 |
| `notion_failed` | Notion 보고서 생성 실패로 이메일 미전송 |
| `skipped_invalid_message_id` | Agent 근거 ID가 원본에 없어 알림 미전송 |
| `not_required` | 위험 단계가 낮아 알림 대상 아님 |

## 해야 할 일

- [x] SMTP 환경변수를 앞뒤 공백 제거 후 읽는다.
- [x] SMTP 설정 누락 시 `AgentError`로 중단한다.
- [x] Notion 링크와 관리자 요약을 포함한 이메일 본문을 만든다.
- [x] SMTP TLS 연결로 이메일을 전송한다.
- [x] 백엔드는 Notion 생성 후 이메일 전송을 실행한다.
- [x] 프론트엔드는 `notification_delivery.status`를 이메일 전달 상태로 표시한다.
- [x] 자동 테스트에서는 fake SMTP로 실제 외부 발송 없이 전송 계약을 검증한다.
- [x] Superdesign REDPLAG Notion 보고서가 실제 Notion에 생성된 뒤 이메일 링크로 전송되는지 확인한다.

## 작업 기록

- 한 일: Notion 링크 SMTP 이메일 전송 모듈 추가, 백엔드 `send_notification`에 Notion 생성 후 이메일 전송 연결, 프론트 알림 상태 의미를 이메일 전송 기준으로 변경. Superdesign REDPLAG Notion 보고서 생성 성공 후 이메일 발송까지 실제 연결 확인
- 바꾼 파일: `ai/notification/email_delivery.py`, `ai/notification/notion_delivery.py`, `back/api.py`, `front/app.js`, `data_schema.md`, `README.md`, `docs/phase_06_backend_to_notification.md`, `docs/phase_07_backend_to_frontend.md`, `docs/phase_08_backend_to_email.md`, `test/test_phase_08_email_notification.py`, `test/test_phase_04_to_06_integration.py`, `test/test_phase_07_frontend_runtime.py`, `test/test_notion_delivery_native_blocks.py`
- 입력과 출력: `notification_email`, Notion 링크, Agent 사건 요약을 받아 `channel=email`, `status=sent` 형식의 `notification_delivery`를 반환
- 확인한 결과: `python3 -m pytest test/test_phase_08_email_notification.py test/test_phase_04_to_06_integration.py test/test_notion_delivery_native_blocks.py test/test_notion_page_format.py -q` 결과 12개 통과. 실제 SMTP 전송 결과 `status=sent`, Notion URL 생성 확인
- 남은 문제: 없음
- 다음 담당자에게 넘길 내용: `notification_delivery`는 Notion 생성 결과가 아니라 이메일 전달 상태다.
