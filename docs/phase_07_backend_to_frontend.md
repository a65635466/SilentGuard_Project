# Phase 07: 백엔드 -> 프론트엔드

## 전달 방향

```text
백엔드 -> 프론트엔드
POST /api/chat/analyze 응답
```

## 넘겨야 하는 데이터

```json
{
  "analysis_id": "analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6",
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "messages": [
    {
      "message_id": "msg_001",
      "sender_id": "A",
      "sender_label": "A",
      "text": "너 왜 또 여기 들어왔냐",
      "created_at": "2026-08-08T14:28:00+09:00"
    }
  ],
  "bullying_probability": 0.91,
  "risk_level": "immediate",
  "incident": {
    "incident_id": "incident_room_20260812143005_a1b2c3_001",
    "risk_chat_segments": [],
    "suspected_risk_types": [],
    "context_reason": "",
    "evidence_message_ids": [],
    "manager_summary": "",
    "missing_context": [],
    "recommended_initial_actions": [],
    "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다."
  },
  "risk_segments": [],
  "agent_response": {
    "status": "completed",
    "summary": "관리자 요약 문장",
    "incident": {},
    "risk_segments": []
  },
  "notification_delivery": {
    "channel": "email",
    "status": "sent",
    "sent_at": "2026-08-11T14:30:10+09:00",
    "external_message_id": "smtp-message-id",
    "notion_url": "https://app.notion.com/p/...",
    "notion_page_id": "notion_page_id",
    "recipient_email": "teacher@example.com"
  }
}
```

## normal/caution일 때

```json
{
  "analysis_id": "analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6",
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "messages": [],
  "bullying_probability": 0.42,
  "risk_level": "normal",
  "incident": {},
  "risk_segments": [],
  "agent_response": {},
  "notification_delivery": {
    "channel": "none",
    "status": "not_required",
    "sent_at": null,
    "external_message_id": null,
    "recipient_email": "teacher@example.com"
  }
}
```

## 필드 기준

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `analysis_id` | string | 예 |
| `room_id` | string | 예 |
| `room_name` | string | 예 |
| `notification_email` | string | 예 |
| `messages` | array | 예 |
| `bullying_probability` | number | 예 |
| `risk_level` | string | 예 |
| `incident` | object | 예 |
| `risk_segments` | array | 예 |
| `agent_response` | object | 예 |
| `notification_delivery` | object | 예 |

`notification_delivery.status`는 알림 전달 상태 화면에서 이메일 전송 상태로 표시한다. 성공은 `sent`, SMTP 설정 누락은 `email_not_configured`, SMTP 전송 실패는 `email_failed`, Notion 생성 실패는 `notion_failed`, 위험도가 낮아 전송하지 않은 경우는 `not_required`다.

## 작업 기록

- 한 일: 최종 분석 응답에 `room_name`, `notification_email`, 이메일 기준 `notification_delivery` 표시 기준 추가
- 바꾼 파일: `data_schema.md`, `docs/phase_07_backend_to_frontend.md`, `back/api.py`, `front/app.js`
- 입력과 출력: 분석 응답이 생성된 채팅방 메타데이터와 이메일 알림 전달 상태를 함께 반환
- 확인한 결과: `python3 -m pytest test -q` 결과 21개 통과
- 남은 문제: 실제 외부 이메일 도착 확인은 로컬 서버에서 위험 분석 실행 필요
- 다음 담당자에게 넘길 내용: 방별 분석 결과 화면은 응답의 `room_id` 기준으로 분리해야 함
