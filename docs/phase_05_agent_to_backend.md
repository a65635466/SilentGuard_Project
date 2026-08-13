# Phase 05: Agent -> 백엔드

## 전달 방향

```text
Agent -> 백엔드
```

## 넘겨야 하는 데이터

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

## 필드 기준

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `incident_id` | string | 예 |
| `risk_chat_segments` | array | 예 |
| `risk_chat_segments[].segment_id` | string | 예 |
| `risk_chat_segments[].start_message_id` | string | 예 |
| `risk_chat_segments[].end_message_id` | string | 예 |
| `risk_chat_segments[].evidence_message_ids` | string array | 예 |
| `risk_chat_segments[].start_at` | ISO-8601 string | 예 |
| `risk_chat_segments[].end_at` | ISO-8601 string | 예 |
| `risk_chat_segments[].reason` | string | 예 |
| `suspected_risk_types` | array | 예 |
| `context_reason` | string | 예 |
| `evidence_message_ids` | string array | 예 |
| `manager_summary` | string | 예 |
| `missing_context` | string array | 예 |
| `recommended_initial_actions` | string array | 예 |
| `disclaimer` | string | 예 |

## 백엔드 변환 기준

```text
risk_chat_segments -> risk_segments
manager_summary -> agent_response.summary
Agent 전체 결과 -> incident
```
