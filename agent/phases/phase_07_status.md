## 현재 사항

- `analyze_chat`: `back/` 백엔드가 프론트엔드에 원본 대화, 위험도, Agent 결과, 알림 상태를 반환한다.
- `create_chat_room`: 채팅방 이름과 이메일을 받아 백엔드가 `room_id`를 생성한다.
- `list_chat_rooms`: 생성된 채팅방 목록을 프론트엔드에 반환한다.
- `test_phase_07_backend_allows_frontend_cors_origin`: `127.0.0.1:5173` CORS 허용을 검증한다.
- `test_phase_07_frontend_calls_backend_absolute_api_url`: `front/app.js`의 백엔드 절대 URL 호출을 검증한다.
- 전체 테스트 17개가 통과했다.

## 문제/막힌 지점

- 없음

## 결정된 사항

- 프론트엔드는 `5173`, 백엔드는 `8000`에서 따로 실행하고 CORS로 연결한다.
- 프론트엔드는 고정 `demo_room` 대신 채팅방 생성 응답의 `room_id`를 분석 요청에 사용한다.
