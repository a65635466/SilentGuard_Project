# Phase 4·5 데이터 스키마 테스트 요약

## 결론

- Agent 입력 계약(`analysis_id`, `room_id`, `bullying_probability`, `risk_level`, `messages`)은 Agent 검증 코드와 맞음.
- Agent 출력 계약(`incident_id`, `risk_chat_segments`, 근거 ID, 관리자 요약 등)은 Agent 검증 코드와 맞음.
- 백엔드의 `build_agent_analysis_request()`는 Phase 4 기준처럼 `analysis_id`를 만들고 `risk_segments`/`incident_id`를 Agent 입력에 넣지 않음.
- 백엔드는 `ai/agent_analysis/silentguard_agent.py`의 `SilentGuardAgent`를 호출함.
- 백엔드 최종 응답은 `data_schema.md` 기준처럼 `analysis_id`, `room_name`, `notification_email`을 포함함.
- `analysis_id`는 `analysis_{room_id}_{yyyyMMddHHmmss}_{short_uuid}` 형식으로 생성되고 Agent 입력, 최종 응답, Notion 입력 payload에 같은 값으로 전달됨.
- 현재 로컬 Python 환경에 테스트 실행에 필요한 requirements 설치는 완료됨.

## 실행 결과

- requirements 설치: 통과
- venv 패키지 정합성 확인(`pip check`): 통과
- 주요 패키지 import 확인: 통과
- compileall: 통과
- 루트 Agent 계약 검증: 통과
- 루트 Agent 사건 출력 검증: 통과
- 백엔드 normal 경로 직접 호출: 통과 (`0.42`, `normal`, Agent 미호출)
- 백엔드 Agent 클래스 로드 확인: 통과 (`_silentguard_root_app.silentguard_agent`)
- 백엔드 `request_agent_analysis()` 실제 OpenAI Agent 호출: 통과 (`status=completed`, 위험 구간 1개, 근거 메시지 ID 2개)
- 현재 통합 pytest: 17개 통과

## 확인된 문제

- 없음

## 다음 조치

- 실제 프론트엔드 연동 시 채팅방 생성 응답의 `room_id`, `analysis_id`, `risk_segments`, `incident`, `notification_delivery.recipient_email` 표시가 `data_schema.md` 기준과 맞는지 확인해야 함.
