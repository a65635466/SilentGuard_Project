# Phase 06: 백엔드 -> Notion 보고서

## 전달 방향

```text
백엔드 -> Notion 보고서 생성 모듈
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
  }
}
```

## Notion 생성 결과 데이터

```json
{
  "channel": "notion",
  "status": "created",
  "sent_at": "2026-08-11T14:30:10+09:00",
  "external_message_id": "notion_page_id",
  "notion_url": "https://app.notion.com/p/...",
  "recipient_email": "teacher@example.com"
}
```

## 현재 연결 방식

`back/api.py`의 `send_notification`은 Agent 결과의 근거 메시지 ID 검증이 통과한 뒤 `ai/notification/notion_delivery.py`의 `create_notion_report_page`를 호출한다.

Notion 보고서는 `.superdesign/design-system.md`에서 확정한 REDPLAG 관리자 검토형 디자인을 기준으로 native Notion block으로 생성한다. 테이블은 Notion API가 받는 `table.children` 아래 `table_row` 구조를 사용한다.

Phase 06의 책임은 Notion 페이지 생성과 생성된 `notion_url`, `notion_page_id` 확보까지다. 최종 API 응답의 `notification_delivery`는 Phase 08에서 이메일 전달 상태를 의미하도록 확장됐다.

채팅방 생성 시 받은 `notification_email`은 Phase 08 이메일 수신 대상으로 알림 payload에 포함한다.

Notion 설정이 없거나 Notion API 호출이 실패하면 분석 결과는 유지하고 Phase 08 기준의 `notion_failed`와 오류 메시지를 반환한다.

## 외부 연결이 없을 때

```json
{
  "channel": "none",
  "status": "notion_failed",
  "sent_at": null,
  "external_message_id": null,
  "recipient_email": "teacher@example.com"
}
```

## 작업 기록

- 한 일: 채팅방의 `room_name`, `notification_email`을 Notion 보고서 payload에 포함하고, Phase 08 이메일 전송의 선행 단계로 정리. Superdesign REDPLAG Notion 디자인을 실제 Notion API native block 생성 구조에 맞게 연결
- 바꾼 파일: `data_schema.md`, `docs/phase_06_backend_to_notification.md`, `back/api.py`, `ai/notification/email_delivery.py`, `ai/notification/notion_delivery.py`, `test/test_phase_04_to_06_integration.py`, `test/test_notion_delivery_native_blocks.py`
- 입력과 출력: 생성된 채팅방 메타데이터를 분석 완료 후 Notion 보고서와 이메일 알림 payload에 병합
- 확인한 결과: `python3 -m pytest test/test_phase_08_email_notification.py test/test_phase_04_to_06_integration.py test/test_notion_delivery_native_blocks.py test/test_notion_page_format.py -q` 결과 12개 통과. 실제 Notion 생성 후 SMTP 이메일 전송 결과 `status=sent` 확인
- 남은 문제: 없음
- 다음 담당자에게 넘길 내용: 최종 `notification_delivery`는 Notion 생성 상태가 아니라 이메일 전달 상태를 의미함
