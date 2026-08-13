# SilentGuard 데이터 흐름과 스키마 기준

## 목적

프론트엔드, 모델, 백엔드, Agent가 어떤 데이터를 주고받는지 한 곳에서 맞추기 위한 문서다.

현재 헷갈리는 핵심은 `analysis_id`, `incident_id`, `risk_segments`의 기준이다. 이 문서는 MVP 기준으로 각 ID가 무엇을 식별하는지, 어느 담당자가 어떤 필드를 만들고 소비하는지 정리한다.

## 한 줄 결론

```text
프론트엔드가 채팅방 이름과 이메일로 채팅방 생성을 요청함
-> 백엔드가 room_id를 만들고 채팅방 메타데이터를 보관함
-> 프론트엔드가 생성된 room_id와 원본 메시지를 보냄
-> 백엔드가 analysis_id를 만들고 모델을 호출함
-> 모델은 bullying_probability 숫자만 반환함
-> 백엔드가 risk_level을 계산함
-> warning 이상이면 백엔드가 Agent에 원본 메시지와 점수, 위험 단계를 넘김
-> Agent가 incident_id, risk_chat_segments, 관리자용 알림 내용을 만듦
-> 백엔드가 Agent 결과를 프론트엔드 응답 형식으로 변환함
-> 프론트엔드가 원본 메시지, 점수, 위험 단계, Agent 결과, 알림 상태를 표시함
```

## ID 기준

### `room_id`

`room_id`는 채팅방 또는 대화 묶음을 식별한다.

같은 채팅방에서 여러 번 분석을 실행해도 `room_id`는 그대로 유지된다.

`room_id`는 백엔드가 만든다. 프론트엔드는 채팅방 생성 응답으로 받은 값을 이후 메시지 입력과 분석 요청에 사용한다.

예시:

```text
room_id = room_20260812143005_a1b2c3
```

### `message_id`

`message_id`는 원본 메시지 한 개를 식별한다.

모델, 백엔드, Agent, 프론트엔드는 모두 같은 `message_id`를 사용한다. Agent가 반환하는 모든 근거 ID는 입력 `messages` 안에 실제로 있어야 한다.

예시:

```text
message_id = msg_001
```

### `analysis_id`

`analysis_id`는 이번 분석 실행 1건을 식별한다.

MVP 기준에서 분석 1건은 아래 기준으로 본다.

```text
백엔드가 유효한 POST /api/chat/analyze 요청을 받아
해당 요청의 messages 묶음에 대해 모델 점수 계산과 위험 단계 계산을 시도한 1회 실행
```

따라서 같은 `room_id`, 같은 `messages`라도 사용자가 분석 버튼을 다시 누르면 새 분석 실행이므로 새 `analysis_id`를 만든다.

```text
첫 번째 분석 버튼 클릭 -> analysis_room_20260812143005_a1b2c3_20260812_001
두 번째 분석 버튼 클릭 -> analysis_room_20260812143005_a1b2c3_20260812_002
```

`analysis_id`는 백엔드가 만든다. 프론트엔드, 모델, Agent가 만들지 않는다.

권장 생성 방식:

```text
analysis_{room_id}_{yyyyMMddHHmmss}_{short_uuid}
```

예시:

```text
analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6
```

### `incident_id`

`incident_id`는 Agent가 만든 사건 1건을 식별한다.

백엔드는 Agent를 호출하기 전에 아직 사건을 판단하지 않았으므로 `incident_id`를 미리 만들지 않는다. Agent가 원본 메시지를 보고 위험 구간과 사건을 구성한 뒤 결과에 포함한다.

예시:

```text
incident_room_20260812143005_a1b2c3_001
```

### `segment_id`

`segment_id`는 Agent가 만든 위험 구간 1개를 식별한다.

백엔드는 위험 구간을 판단하지 않으므로 `segment_id`도 만들지 않는다.

예시:

```text
seg_001
```

## 공통 메시지 스키마

모든 담당자는 메시지 원본을 아래 형식으로 맞춘다.

```json
{
  "message_id": "msg_001",
  "sender_id": "A",
  "sender_label": "A",
  "text": "너 왜 또 여기 들어왔냐",
  "created_at": "2026-08-08T14:28:00+09:00"
}
```

필드 기준:

| 필드 | 타입 | 생성 담당 | 설명 |
| --- | --- | --- | --- |
| `message_id` | string | 프론트엔드 또는 샘플 데이터 | 원본 메시지 ID |
| `sender_id` | string | 프론트엔드 또는 샘플 데이터 | 발신자 내부 ID |
| `sender_label` | string | 프론트엔드 또는 샘플 데이터 | 화면 표시용 이름 |
| `text` | string | 프론트엔드 또는 샘플 데이터 | 원본 문장 |
| `created_at` | ISO-8601 string | 프론트엔드 또는 샘플 데이터 | 메시지 생성 시간 |

원칙:

- 원본 `text`는 줄이거나 고쳐 쓰지 않는다.
- `created_at`은 ISO-8601 형식으로 맞춘다.
- 같은 분석 요청 안에서 `message_id`는 중복되면 안 된다.

## 1. 프론트엔드 -> 백엔드: 채팅방 생성

API:

```text
POST /api/chat/rooms
```

요청 body:

```json
{
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com"
}
```

응답 body:

```json
{
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "created_at": "2026-08-12T14:30:05+09:00"
}
```

필드 기준:

| 필드 | 타입 | 생성 담당 | 설명 |
| --- | --- | --- | --- |
| `room_id` | string | 백엔드 | 채팅방 ID |
| `room_name` | string | 프론트엔드 입력 | 사용자가 입력한 채팅방 이름 |
| `notification_email` | string | 프론트엔드 입력 | Notion 링크 알림을 받을 이메일 |
| `created_at` | ISO-8601 string | 백엔드 | 채팅방 생성 시간 |

원칙:

- `room_name`은 공백일 수 없다.
- `notification_email`은 필수이며 기본 이메일 형식을 만족해야 한다.
- 프론트엔드는 `room_id`를 만들지 않는다.
- MVP에서는 운영 DB 없이 백엔드 메모리 저장소에 채팅방 메타데이터를 보관한다.

## 2. 프론트엔드 -> 백엔드: 채팅 분석

API:

```text
POST /api/chat/analyze
```

요청 body:

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

프론트엔드가 하는 일:

- 채팅 입력을 `messages` 배열로 만든다.
- 채팅방 생성 응답으로 받은 `room_id`를 함께 보낸다.
- `notification_email`은 분석 요청에 다시 보내지 않는다.
- 분석 결과를 받기 전 이전 결과와 섞이지 않게 화면 상태를 초기화한다.

프론트엔드가 하지 않는 일:

- `analysis_id`를 만들지 않는다.
- `bullying_probability`를 만들지 않는다.
- `risk_level`을 계산하지 않는다.
- 위험 구간이나 사건을 만들지 않는다.

## 3. 백엔드 -> 모델

모델 입력:

```json
{
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

모델 출력:

```json
{
  "bullying_probability": 0.91
}
```

모델이 하는 일:

- 메시지 묶음을 보고 `0` 이상 `1` 이하의 숫자만 반환한다.

모델이 하지 않는 일:

- 위험 단계를 계산하지 않는다.
- 위험 구간을 만들지 않는다.
- 사건 요약이나 알림 문구를 만들지 않는다.
- 가해자, 피해자, 학교폭력 여부를 확정하지 않는다.

## 4. 백엔드 내부 계산

백엔드는 모델의 `bullying_probability`를 받아 `risk_level`을 계산한다.

```text
0.00 <= probability < 0.50 = normal
0.50 <= probability < 0.70 = caution
0.70 <= probability < 0.85 = warning
0.85 <= probability <= 1.00 = immediate
```

백엔드가 만드는 값:

```json
{
  "analysis_id": "analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6",
  "bullying_probability": 0.91,
  "risk_level": "immediate"
}
```

Agent 호출 기준:

```text
normal -> Agent 호출 안 함
caution -> Agent 호출 안 함
warning -> Agent 호출함
immediate -> Agent 호출함
```

## 5. 백엔드 -> Agent

Agent 입력은 아래 형식을 기준으로 한다.

```json
{
  "analysis_id": "analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6",
  "room_id": "room_20260812143005_a1b2c3",
  "bullying_probability": 0.91,
  "risk_level": "immediate",
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

중요한 제외 필드:

```text
risk_segments는 Agent 입력에 넣지 않는다.
incident_id는 Agent 입력에 넣지 않는다.
```

이유:

- `risk_segments`는 Agent가 원본 메시지를 보고 만드는 결과다.
- `incident_id`는 Agent가 사건을 만든 뒤 붙이는 결과 ID다.
- 백엔드가 이 값을 미리 넣으면 백엔드가 위험 구간이나 사건을 판단하는 것처럼 역할이 섞인다.

## 6. Agent -> 백엔드

Agent는 사건과 관리자용 표준 알림 JSON을 반환한다.

Agent 표준 출력:

```json
{
  "incident_id": "incident_room_20260812143005_a1b2c3_001",
  "risk_chat_segments": [
    {
      "segment_id": "seg_001",
      "start_message_id": "msg_001",
      "end_message_id": "msg_004",
      "evidence_message_ids": ["msg_001", "msg_003", "msg_004"],
      "start_at": "2026-08-08T14:28:00+09:00",
      "end_at": "2026-08-08T14:30:00+09:00",
      "reason": "특정 사용자를 향해 대화에서 나가라고 요구하는 흐름이 이어져 추가 확인이 필요합니다."
    }
  ],
  "suspected_risk_types": [
    {
      "type": "배제성",
      "evidence_message_ids": ["msg_003", "msg_004"]
    }
  ],
  "context_reason": "대화 참여자들이 특정 사용자의 참여를 막는 표현을 반복해 추가 검토가 필요합니다.",
  "evidence_message_ids": ["msg_001", "msg_003", "msg_004"],
  "manager_summary": "14:28~14:30 사이 특정 사용자를 대화에서 배제하는 표현이 반복되었습니다. 전후 대화와 당사자 상황을 함께 확인해야 합니다.",
  "missing_context": [
    "대화 이전에 어떤 일이 있었는지 확인하지 못했습니다."
  ],
  "recommended_initial_actions": [
    "원본 메시지와 앞뒤 대화를 함께 확인합니다.",
    "관련 메시지를 보존합니다."
  ],
  "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다."
}
```

Agent가 하는 일:

- 위험 구간을 `risk_chat_segments`로 만든다.
- 관련 구간을 하나의 `incident_id` 사건으로 묶는다.
- 위험 유형, 맥락 이유, 근거 메시지 ID, 관리자 요약, 누락 맥락, 초기 조치를 만든다.

Agent가 하지 않는 일:

- 모델 점수를 만들지 않는다.
- 백엔드 위험 단계를 다시 계산하지 않는다.
- 원본에 없는 의도나 과거 사건을 만들지 않는다.
- 가해자, 피해자, 학교폭력 여부를 확정하지 않는다.

## 7. 백엔드 내부 변환

백엔드는 Agent 표준 출력을 프론트엔드 응답에 맞게 감싼다.

변환 기준:

```text
Agent risk_chat_segments -> 백엔드 risk_segments
Agent manager_summary -> 백엔드 agent_response.summary
Agent 전체 결과 -> 백엔드 incident와 agent_response.incident에 보존
```

권장 백엔드 내부 `agent_response`:

```json
{
  "status": "completed",
  "summary": "14:28~14:30 사이 특정 사용자를 대화에서 배제하는 표현이 반복되었습니다. 전후 대화와 당사자 상황을 함께 확인해야 합니다.",
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
  "risk_segments": []
}
```

## 8. 백엔드 -> Notion/이메일 알림

첫 MVP에서 외부 알림은 분석을 하지 않는다. 검증된 Agent 결과를 보고서 또는 알림 형식으로 전달만 한다.

Notion 보고서 생성 입력:

```json
{
  "analysis_id": "analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6",
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "messages": [],
  "bullying_probability": 0.91,
  "risk_level": "immediate",
  "incident": {}
}
```

이메일 알림 전달 성공 결과:

```json
{
  "channel": "email",
  "status": "sent",
  "sent_at": "2026-08-11T14:30:10+09:00",
  "external_message_id": "smtp-message-id",
  "notion_url": "https://app.notion.com/p/...",
  "notion_page_id": "notion_page_id",
  "recipient_email": "teacher@example.com"
}
```

`notification_delivery`는 Notion 문서 생성 여부가 아니라, 생성된 Notion 링크가 이메일로 전달됐는지를 나타낸다.

알림 대상이 아닐 때:

```json
{
  "channel": "none",
  "status": "not_required",
  "sent_at": null,
  "external_message_id": null,
  "recipient_email": "teacher@example.com"
}
```

SMTP 설정이 없으면 `email_not_configured`, SMTP 전송이 실패하면 `email_failed`, Notion 문서 생성이 실패하면 `notion_failed`를 사용한다.

## 9. 백엔드 -> 프론트엔드 최종 응답

권장 최종 응답:

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

프론트엔드 표시 기준:

- `messages`: 원본 대화 표시
- `room_name`, `notification_email`: 선택된 채팅방 정보 표시
- `bullying_probability`: 위험 가능성 표시
- `risk_level`: 위험 단계 표시
- `risk_segments`: 위험 구간 표시
- `incident`: 관리자용 사건 알림 표시
- `notification_delivery`: 알림 전달 상태 표시

## normal/caution 응답 기준

`normal`, `caution`에서는 Agent를 호출하지 않는다.

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

## 오류 처리 기준

### 입력 오류

채팅방 생성 시 이메일이 없으면 채팅방을 만들지 않는다.

```json
{
  "detail": "notification_email is required",
  "error_code": "room_email_required",
  "user_message": "Notion 링크를 받을 이메일을 입력해주세요."
}
```

`room_id`가 없거나 `messages`가 비어 있으면 분석하지 않는다.

```json
{
  "detail": "room_id is required",
  "error_code": "room_id_required",
  "user_message": "채팅방을 먼저 선택해주세요."
}
```

```json
{
  "detail": "messages must not be empty",
  "error_code": "input_required",
  "user_message": "분석할 채팅을 입력해주세요."
}
```

생성되지 않은 `room_id`로 분석을 요청하면 분석하지 않는다.

```json
{
  "detail": "chat room not found",
  "error_code": "room_not_found",
  "user_message": "채팅방을 먼저 생성해주세요."
}
```

### 모델 실패

모델 호출이 실패하면 Agent를 호출하지 않는다.

```json
{
  "detail": "model scoring failed",
  "error_code": "model_retryable_error",
  "retryable": true,
  "user_message": "모델 분석에 실패했습니다. 다시 시도해주세요."
}
```

### Agent 실패

Agent 호출이 실패해도 원본 메시지, 확률, 위험 단계는 유지한다.

```json
{
  "agent_response": {
    "status": "agent_failed",
    "retryable": true
  },
  "incident": {},
  "risk_segments": []
}
```

### Agent 근거 ID 오류

Agent가 입력에 없는 메시지 ID를 반환하면 외부 알림을 만들지 않는다.

```json
{
  "notification_delivery": {
    "channel": "none",
    "status": "skipped_invalid_message_id",
    "sent_at": null,
    "external_message_id": null,
    "recipient_email": "teacher@example.com"
  }
}
```

### Notion 또는 이메일 알림 실패

Notion 생성이나 이메일 전송이 실패해도 사건과 Agent 결과는 유지한다.

```json
{
  "notification_delivery": {
    "channel": "email",
    "status": "email_failed",
    "sent_at": null,
    "external_message_id": null,
    "notion_url": "https://app.notion.com/p/...",
    "recipient_email": "teacher@example.com"
  }
}
```

## 담당자별 소유 필드

| 필드 | 생성 담당 | 소비 담당 | 비고 |
| --- | --- | --- | --- |
| `room_id` | 백엔드 | 백엔드, Agent, 프론트엔드 | 채팅방 식별 |
| `room_name` | 프론트엔드 입력, 백엔드 보관 | 백엔드, Notion, 프론트엔드 | 채팅방 표시 이름 |
| `notification_email` | 프론트엔드 입력, 백엔드 보관 | 백엔드, 알림, 프론트엔드 | Notion 링크 알림 수신 이메일 |
| `message_id` | 프론트엔드 또는 샘플 데이터 | 전체 | 근거 연결의 기준 |
| `analysis_id` | 백엔드 | Agent, Notion, 프론트엔드 | 분석 실행 1건 |
| `bullying_probability` | 모델 | 백엔드, Agent, 프론트엔드 | 0~1 숫자 |
| `risk_level` | 백엔드 | Agent, 프론트엔드 | 4단계 |
| `risk_chat_segments` | Agent | 백엔드 | Agent 표준 출력 |
| `risk_segments` | 백엔드 변환 | 프론트엔드 | Agent 결과를 표시용으로 옮긴 값 |
| `incident_id` | Agent | 백엔드, Notion, 프론트엔드 | 사건 식별 |
| `manager_summary` | Agent | 백엔드, 프론트엔드, Notion | 관리자 요약 |
| `notification_delivery` | 백엔드 또는 알림 모듈 | 프론트엔드 | 이메일 전달 상태 |
| `notion_url` | Notion 생성 모듈 | 백엔드, 프론트엔드 | 보고서 링크 |

## 정리 완료된 충돌 기록

2026-08-12 사용자 결정으로 채팅방 생성 시 `room_name`, `notification_email`을 필수로 받고, `room_id`는 백엔드가 생성하는 구조를 최신 기준으로 확정했다.

같은 날 로컬 문서와 Notion 담당 문서의 예전 단일 채팅방 흐름을 최신 기준으로 맞췄다.

정리된 기준:

- 프론트엔드는 `POST /api/chat/rooms`로 채팅방을 먼저 생성한다.
- 백엔드는 `room_id`, `analysis_id`를 생성한다.
- 프론트엔드는 생성된 `room_id`로 `POST /api/chat/analyze`를 호출한다.
- 백엔드 -> Agent 입력에는 `incident_id`, `risk_segments`, `risk_chat_segments`, `incident`를 넣지 않는다.
- 백엔드 -> Agent 입력에는 `analysis_id`, `room_id`, `bullying_probability`, `risk_level`, `messages`만 넣는다.
- Agent 출력 `risk_chat_segments`는 백엔드 최종 응답에서 `risk_segments`로 변환한다.
- Notion 보고서와 이메일 알림 payload에는 `room_name`, `notification_email`을 포함한다.
- 프론트엔드는 `notification_delivery.status`를 이메일 전달 상태로 표시한다.
