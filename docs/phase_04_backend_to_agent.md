# Phase 04: 백엔드 -> Agent

## 전달 방향

```text
백엔드 -> Agent
warning 또는 immediate일 때만 호출
```

## 넘겨야 하는 데이터

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

## 필드 기준

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `analysis_id` | string | 예 |
| `room_id` | string | 예 |
| `bullying_probability` | number | 예 |
| `risk_level` | string | 예 |
| `messages` | array | 예 |
| `messages[].message_id` | string | 예 |
| `messages[].sender_id` | string | 예 |
| `messages[].sender_label` | string | 예 |
| `messages[].text` | string | 예 |
| `messages[].created_at` | ISO-8601 string | 예 |

## 넣지 않는 값

- `risk_segments`
- `risk_chat_segments`
- `incident_id`
- `incident`
