# 프론트엔드 작업 요청: 채팅방 생성과 이메일 입력 연동

## 작업 목적

SilentGuard MVP에 채팅방 단위 흐름을 추가한다.

프론트엔드는 사용자가 채팅방을 먼저 만들고, 해당 채팅방 안에서 메시지 입력과 분석 결과 확인을 하도록 상태를 나눈다. 채팅방 생성 시 Notion 링크를 받을 이메일은 필수로 입력받는다.

이번 작업에서 프론트엔드는 분석 결과, 위험 단계, 위험 구간, 사건, 알림 상태를 직접 만들지 않는다. 기존 기준대로 백엔드 응답을 화면에 표시한다.

## 핵심 변경 요약

- 기존 고정값 `room_id: "demo_room"` 사용을 제거한다.
- 채팅방 생성 화면 또는 입력 흐름을 추가한다.
- 채팅방 생성 시 `room_name`, `notification_email`을 백엔드로 보낸다.
- 백엔드가 반환한 `room_id`를 선택된 채팅방 상태로 저장한다.
- 채팅방별로 메시지 목록과 분석 결과를 분리해서 관리한다.
- 분석 요청은 선택된 채팅방의 `room_id`와 해당 방의 `messages`만 보낸다.

## 백엔드 API 계약

### 1. 채팅방 생성

```text
POST http://127.0.0.1:8000/api/chat/rooms
```

요청 body:

```json
{
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com"
}
```

필드 기준:

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `room_name` | string | 예 | 사용자가 입력하는 채팅방 이름 |
| `notification_email` | string | 예 | Notion 링크를 받을 이메일 |

응답 body:

```json
{
  "room_id": "room_20260812143005_a1b2c3",
  "room_name": "1학년 3반 단체방",
  "notification_email": "teacher@example.com",
  "created_at": "2026-08-12T14:30:05+09:00"
}
```

프론트엔드 처리:

- `room_id`는 프론트엔드가 만들지 않는다.
- 응답받은 채팅방 객체를 프론트 상태에 저장한다.
- 생성 직후 해당 채팅방을 현재 선택된 채팅방으로 설정한다.
- 이메일은 방 생성 시 필수 입력으로 검증한다.

### 2. 채팅방 목록 조회

```text
GET http://127.0.0.1:8000/api/chat/rooms
```

응답 body:

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

프론트엔드 처리:

- 초기 진입 시 이미 생성된 채팅방 목록이 필요하면 이 API를 호출한다.
- MVP 메모리 저장소 기준이라 백엔드 서버를 재시작하면 목록은 초기화될 수 있다.

### 3. 채팅 분석

```text
POST http://127.0.0.1:8000/api/chat/analyze
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
      "created_at": "2026-08-12T14:31:00+09:00"
    }
  ]
}
```

프론트엔드 처리:

- `room_id`는 현재 선택된 채팅방의 값을 사용한다.
- `notification_email`은 분석 요청에 다시 보내지 않는다.
- 분석 전에 선택된 채팅방이 없으면 분석 요청을 보내지 않는다.
- 분석 전에 해당 채팅방의 메시지가 비어 있으면 분석 요청을 보내지 않는다.

## 프론트엔드 상태 구조 제안

현재 `front/app.js`는 전역 `messages` 하나와 고정 `demo_room` 기준으로 동작한다. 채팅방 기능을 넣을 때는 아래처럼 방별 상태로 나누는 것을 권장한다.

```js
let chatRooms = [];
let selectedRoomId = null;
let roomMessagesById = {};
let roomAnalysisById = {};
```

예시:

```js
chatRooms = [
    {
        room_id: "room_20260812143005_a1b2c3",
        room_name: "1학년 3반 단체방",
        notification_email: "teacher@example.com",
        created_at: "2026-08-12T14:30:05+09:00"
    }
];

roomMessagesById = {
    room_20260812143005_a1b2c3: []
};

roomAnalysisById = {
    room_20260812143005_a1b2c3: null
};
```

## 현재 코드에서 바꿔야 하는 지점

### `front/app.js`

- `analyzeApiUrl` 옆에 채팅방 생성 API URL을 추가한다.

```js
const createRoomApiUrl = "http://127.0.0.1:8000/api/chat/rooms";
```

- 현재 전역 `messages`를 선택된 채팅방 기준으로 가져오도록 바꾼다.
- `buildAnalyzeRequest()`의 고정 `room_id: "demo_room"`을 제거한다.
- `buildAnalyzeRequest()`는 현재 선택된 채팅방 ID를 사용한다.

변경 방향:

```js
function buildAnalyzeRequest() {
    const selectedMessages = getSelectedRoomMessages();

    return {
        room_id: selectedRoomId,
        messages: selectedMessages.map((message) => ({
            message_id: message.message_id,
            sender_id: message.sender_id,
            sender_label: message.sender_label,
            text: message.text,
            created_at: message.created_at
        }))
    };
}
```

- 샘플 대화 로드, 메시지 추가, 일괄 입력, 분석 결과 초기화도 선택된 채팅방 기준으로 동작해야 한다.
- 방을 바꿀 때는 해당 방의 메시지와 분석 결과를 다시 렌더링한다.

### `front/index.html`

- 채팅방 생성 입력 UI가 필요하다.
- 최소 입력 필드:
  - 채팅방 이름
  - 알림 이메일
  - 채팅방 생성 버튼
- 채팅방 목록 또는 선택 UI가 필요하다.
- 선택된 채팅방 이름과 이메일을 사용자가 확인할 수 있어야 한다.

### `front/style.css`

- 채팅방 생성 영역, 채팅방 목록, 선택된 채팅방 표시 영역 스타일을 추가한다.
- 기존 채팅/분석 화면의 정보 밀도를 유지한다.

## 입력 검증 기준

프론트엔드는 백엔드 요청 전에 최소 검증만 한다.

- `room_name`은 공백만 있으면 안 된다.
- `notification_email`은 공백만 있으면 안 된다.
- 이메일은 기본 형식 검증을 한다.
- 채팅방이 선택되지 않았으면 메시지 추가와 분석을 막는다.
- 메시지가 없는 채팅방은 분석 요청을 보내지 않는다.

최종 검증은 백엔드가 다시 수행한다.

## 화면 동작 기준

1. 사용자가 채팅방 이름과 이메일을 입력한다.
2. 사용자가 채팅방 생성을 누른다.
3. 프론트엔드는 `POST /api/chat/rooms`를 호출한다.
4. 성공하면 응답받은 채팅방을 목록에 추가하고 현재 채팅방으로 선택한다.
5. 사용자는 선택된 채팅방에서 메시지를 입력하거나 샘플 대화를 불러온다.
6. 사용자가 분석 시작을 누른다.
7. 프론트엔드는 `POST /api/chat/analyze`에 현재 `room_id`와 해당 방의 메시지를 보낸다.
8. 응답받은 분석 결과는 해당 채팅방의 결과 상태에 저장하고 결과 화면에 표시한다.
9. 다른 채팅방으로 이동하면 그 방의 메시지와 분석 결과를 표시한다.

## 프론트엔드가 만들지 않는 값

아래 값은 프론트엔드에서 생성하거나 계산하지 않는다.

- `room_id`
- `analysis_id`
- `bullying_probability`
- `risk_level`
- `incident`
- `risk_segments`
- `agent_response`
- `notification_delivery`
- `notion_url`

## 완료 기준

- 채팅방 이름과 이메일 없이는 채팅방을 만들 수 없다.
- 채팅방 생성 성공 후 백엔드 응답의 `room_id`를 사용한다.
- 채팅방별로 메시지 목록이 섞이지 않는다.
- 채팅방별로 분석 결과가 섞이지 않는다.
- 분석 요청에서 더 이상 `"demo_room"` 고정값을 보내지 않는다.
- 분석 응답의 기존 표시 항목은 유지된다.
- Notion 링크 또는 알림 전달 상태는 백엔드 응답의 `notification_delivery`만 표시한다.

## 백엔드 담당자와 맞춰야 할 점

- `POST /api/chat/rooms`의 최종 경로와 필드명을 위 계약으로 확정한다.
- 채팅방 생성 실패 시 오류 응답 형식을 공유한다.
- 실제 이메일 전송 기능은 아직 미구현이며, 현재는 백엔드가 `notification_delivery.recipient_email`로 수신 대상 이메일을 내려준다.
- MVP에서는 새로고침 후 채팅방 상태를 유지하지 않아도 되는지 확인한다.
