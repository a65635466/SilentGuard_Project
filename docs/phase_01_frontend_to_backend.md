# Phase 01: 프론트엔드 -> 백엔드

## 전달 방향

```text
프론트엔드 -> 백엔드
POST /api/chat/rooms
GET /api/chat/rooms
POST /api/chat/analyze
```

## 1. 채팅방 생성

프론트엔드는 메시지 분석 전에 채팅방을 먼저 만든다. 채팅방별 Notion 링크 수신 이메일은 생성 시 필수로 보낸다.

요청:

```json
{
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com"
}
```

응답:

```json
{
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "created_at": "2026-08-12T14:30:05+09:00"
}
```

채팅방 목록 조회:

```text
GET /api/chat/rooms
```

응답:

```json
[
  {
    "room_id": "room_20260812143005_a1b2c3",
    "room_name": "1학년 3반 단체방",
    "notification_email": "teacher@example.com",
    "created_at": "2026-08-12T14:30:05+09:00"
  }
]
```

## 2. 채팅 분석

## 넘겨야 하는 데이터

```json
{
  "room_id": "room_20260812143005_a1b2c3",
  "messages": [
    {
      "message_id": "msg_001",
      "sender_id": "A",
      "sender_label": "A",
      "text": "너 왜 또 여기 들어왔냐",
      "created_at": "2026-08-08T14:28:00+09:00"
    }
  ]
}
```

## 필드 기준

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `room_name` | string | 채팅방 생성 시 예 |
| `notification_email` | string | 채팅방 생성 시 예 |
| `room_id` | string | 예 |
| `messages` | array | 예 |
| `messages[].message_id` | string | 예 |
| `messages[].sender_id` | string | 예 |
| `messages[].sender_label` | string | 예 |
| `messages[].text` | string | 예 |
| `messages[].created_at` | ISO-8601 string | 예 |

## 프론트엔드가 만들지 않는 값

- `room_id`: 채팅방 생성 응답에서 받은 값을 사용하고 직접 만들지 않는다.
- `analysis_id`
- `bullying_probability`
- `risk_level`
- `risk_segments`
- `incident`

## 작업 기록

- 한 일: 채팅방 생성, 채팅방 목록 조회, 생성된 `room_id` 기반 분석 요청 계약 추가
- 바꾼 파일: `data_schema.md`, `docs/phase_01_frontend_to_backend.md`, `back/api.py`, `test/test_phase_01_to_03_api_contract.py`
- 입력과 출력: `room_name`, `notification_email` 입력을 받아 백엔드가 `room_id`, `created_at`을 포함한 채팅방 객체를 반환
- 확인한 결과: `python3 -m pytest test -q` 결과 17개 통과
- 남은 문제: 실제 이메일 발송은 MVP 현재 단계에서 미구현
- 다음 담당자에게 넘길 내용: 프론트엔드는 고정 `demo_room` 대신 채팅방 생성 응답의 `room_id`를 분석 요청에 사용해야 함
