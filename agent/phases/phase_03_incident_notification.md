# Phase 03: 사건과 표준 알림 JSON

## 목표

관련 위험 구간을 관리자 검토 단위인 사건으로 묶고 표준 알림을 만든다.

## 해야 할 일

- [x] 같은 채팅방인지 확인한다.
- [x] 같은 대상 또는 관계 흐름인지 확인한다.
- [x] 위험 유형이 유사한지 확인한다.
- [x] 시간상 연결되는지 확인한다.
- [x] 위험 유형, 이유, 관리자 요약을 작성한다.
- [x] 누락 맥락과 초기 조치를 작성한다.
- [x] disclaimer를 포함한다.

## 구현 위치

- 실제 코드는 `ai/agent_analysis/`, `ai/notification/`, `ai/schemas/` 폴더에 둔다.
- 사건 출력 생성과 검증은 `ai/agent_analysis/silentguard_agent.py`, `ai/notification/incident_notification.py`에 둔다.
- 현재 로컬 API 요청은 `back/api.py`가 Agent를 호출한다.

## 검증 방법

```bash
python3 -m pytest test -q
python3 -m back.run_local_demo
```

프론트엔드는 별도 정적 서버에서 열고, 백엔드 `http://127.0.0.1:8000` API를 CORS로 호출한다.

## 완료 조건

관리자가 원본과 요약을 함께 보고 다음 확인 행동을 정할 수 있다.
