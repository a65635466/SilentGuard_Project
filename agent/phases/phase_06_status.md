## 현재 사항

- `build_notification_delivery`: 외부 전송 미설정 상태를 표준 알림 전달 결과로 만든다.
- `send_notification`: 검증된 Agent 사건을 Notion 생성 모듈에 넘기고 `recipient_email`이 포함된 알림 상태를 반환한다.
- 전체 테스트 17개가 통과했다.

## 문제/막힌 지점

- 실제 이메일 전송은 아직 연결하지 않았다.

## 결정된 사항

- 채팅방 생성 시 받은 `notification_email`은 `notification_delivery.recipient_email`으로 표시한다.
