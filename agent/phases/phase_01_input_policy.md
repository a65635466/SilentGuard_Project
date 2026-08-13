# Phase 01: 입력 계약과 안전 정책

## 목표

Agent가 어떤 입력을 받고 어떤 판단을 하지 않아야 하는지 고정한다.

## 해야 할 일

- [x] `analysis_id`, `room_id`, 확률, 위험도, 원본 메시지 입력을 정의한다.
- [x] 출력 필드 이름을 고정한다.
- [x] 최종 판정 금지 문구를 정한다.
- [x] 원문 사실과 Agent 해석을 분리한다.
- [x] 근거 ID가 실제 입력에 있어야 한다는 규칙을 넣는다.

## 로컬 MVP 합의

첫 결과물은 서버 배포 없이 로컬에서 실행되는 데모로 만든다. 최종 시연 때는 모델, 백엔드, Agent, 프론트엔드 담당자의 파일을 하나의 프로젝트 폴더에 합쳐 실행한다.

기본 폴더는 아래처럼 나눈다.

```text
ai/model/
back/
ai/agent_analysis/
ai/notification/
ai/schemas/
front/
docs/
```

각 담당자는 자기 폴더 안에서 작업하고, 다른 영역과는 정해진 JSON 형식으로만 연결한다. 첫 MVP에서는 실제 DB, 로그인, 서버 배포, 실제 외부 알림 전송을 하지 않는다.

## 현재 적용할 임시 계약

완벽한 사건 묶음 기준을 먼저 백엔드에 넣지 않고, MVP에서는 아래처럼 진행한다. 이 계약은 실제 실행 결과를 본 뒤 변경할 수 있다.

### 백엔드에서 Agent로 보내는 입력

백엔드는 사건을 만들지 않는다. `analysis_id`는 이번 분석 요청을 추적하기 위한 기술적 ID이며 사건 ID가 아니다.

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

`messages`는 백엔드가 위험하다고 선별한 목록이 아니라, 모델 분석에 사용한 원본 문맥 묶음이다. MVP의 문맥 크기는 최근 5개를 모델에 사용하고, `warning` 이상이면 최근 10개를 Agent에 전달하는 임시값으로 둔다.

### Agent의 책임과 출력

Agent는 입력 문맥 안에서 위험 구간을 선택하고, 관련 구간을 하나의 사건으로 묶을지 판단한다. Agent 입력에는 `incident_id`를 넣지 않는다.

```json
{
  "incident_id": "incident_room_20260812143005_a1b2c3_001",
  "risk_chat_segments": [
    {
      "segment_id": "seg_001",
      "start_message_id": "msg_001",
      "end_message_id": "msg_005",
      "evidence_message_ids": ["msg_001", "msg_004"],
      "start_at": "2026-08-08T14:28:00+09:00",
      "end_at": "2026-08-08T14:30:00+09:00",
      "reason": "특정 사용자를 향해 반복적으로 나가라고 압박하는 대화입니다."
    }
  ],
  "suspected_risk_types": [
    {
      "type": "배제성",
      "evidence_message_ids": ["msg_001", "msg_004"]
    }
  ],
  "context_reason": "",
  "evidence_message_ids": [],
  "manager_summary": "",
  "missing_context": [],
  "recommended_initial_actions": [],
  "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다."
}
```

`incident_id`는 Agent가 사건을 구성한 뒤 생성한다. 표준 알림 필드인 `risk_chat_segments`, `suspected_risk_types`, `context_reason`, `evidence_message_ids`, `manager_summary`, `missing_context`, `recommended_initial_actions`, `disclaimer`는 최상위에 둔다. `suspected_risk_types`는 사건의 구성 여부가 아니라 사건에서 확인되는 위험 유형과 근거를 나타낸다.

## 금지 표현

Agent는 아래 표현을 쓰지 않는다.

- 학교폭력 사건입니다.
- A는 가해자입니다.
- B는 피해자입니다.
- 반드시 처벌해야 합니다.
- A가 악의적으로 행동했습니다.

Agent는 원문에서 확인되는 사실과 자동 분석 해석을 분리해서 쓴다. 확인하지 못한 의도, 과거 사건, 관계를 만들어내지 않는다.

## 근거 ID 규칙

`evidence_message_ids`, 위험 구간의 시작·종료 메시지 ID는 반드시 입력 `messages` 안에 실제로 존재해야 한다. 입력에 없는 ID를 만들거나 원본 문장, 시간, 메시지 ID를 바꾸지 않는다.

## Phase 1 결과

- 백엔드가 Agent에 넘기는 입력 계약을 확정했다.
- `incident_id`는 백엔드 입력이 아니라 Agent 출력으로 정했다.
- Agent 표준 출력 필드를 최상위에 두기로 정했다.
- 로컬 MVP 폴더 구조와 배포 제외 범위를 정했다.
- 최종 판정, 가해자·피해자 확정, 입력에 없는 사실 생성 금지를 안전 정책으로 정했다.

## 남은 문제
 
- 모델 최근 5개, Agent 최근 10개라는 문맥 크기는 임시값이다.
- 구간 분리 품질과 시간 간격 기준은 Phase 2에서 다룬다.

## 완료 조건
Agent 입력 계약, 출력 필드, 안전 금지 규칙, 근거 ID 규칙이 문서에 고정되어 있다.
