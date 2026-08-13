# SilentGuard CORS 실행 구조와 디렉토리 정리 설계

> **현재 상태:** 이 설계의 디렉토리 구조는 유지된다. 최신 API 계약은 채팅방 생성 `POST /api/chat/rooms`, 채팅방 목록 `GET /api/chat/rooms`, 분석 `POST /api/chat/analyze` 순서이며, 채팅방 생성 시 `notification_email`은 필수다.

## 목적

SilentGuard MVP를 프론트엔드와 백엔드가 로컬 CORS로 통신하는 구조로 정리한다. 기존 임시 통합 과정에서 생긴 `app/frontend`와 `Nvidia_test` 의존을 제거하고, 프로젝트 전체 문서와 AI 담당 문서를 구분한다.

## 확정된 루트 구조

```text
silentguard/
├── front/
├── back/
├── ai/
├── agent/
│   └── phases/
├── docs/
│   ├── phase_01_frontend_to_backend.md
│   ├── phase_02_backend_to_model.md
│   ├── phase_03_model_to_backend.md
│   ├── phase_04_backend_to_agent.md
│   ├── phase_05_agent_to_backend.md
│   ├── phase_06_backend_to_notification.md
│   ├── phase_07_backend_to_frontend.md
│   └── superpowers/
├── legacy/
│   └── Nvidia_test/
├── test/
├── data_schema.md
├── AGENTS.md
├── README.md
└── requirements.txt
```

## 디렉토리 역할

`front/`는 브라우저에서 실행되는 프론트엔드 정적 파일을 둔다. 로컬 테스트에서는 `127.0.0.1:5173`에서 실행한다.

`back/`은 FastAPI 서버와 HTTP 요청/응답, CORS, 위험 단계 계산, AI 모듈 호출 조립을 맡는다. 로컬 테스트에서는 `127.0.0.1:8000`에서 실행한다.

`ai/`는 모델 mock, Agent 분석, 사건 구성, 알림 포맷, OpenAI 설정 정규화 등 AI 관련 런타임 코드를 둔다. 프론트엔드 정적 파일은 두지 않는다.

`agent/phases/`는 AI 담당자의 전용 phase 기록이므로 유지한다. 루트 프로젝트 연결 phase 문서는 여기에 두지 않는다.

`docs/`는 프로젝트 전체 연결 phase 문서를 둔다. 기존 `agent/docs/`의 phase 문서는 루트 `docs/`로 이동한다.

`data_schema.md`는 프로젝트 전체 데이터 계약의 기준 문서다. 기존 `agent/data_schema.md`를 루트로 이동하고, 모든 영역은 이 파일을 기준으로 입출력을 판단한다.

`test/`는 실제 자동 테스트 코드와 phase별 실행 결과 Markdown을 둔다. 테스트할 내용은 `docs/phase_*.md`에 phase별로 기록한다.

`legacy/Nvidia_test/`는 기존 NVIDIA 관련 코드, 문서, 테스트를 보존하는 위치다. 현재 실행 구조에는 직접 연결하지 않는다.

## CORS 실행 방식

프론트엔드와 백엔드는 별도 로컬 서버로 실행한다.

```text
브라우저
-> http://127.0.0.1:5173
-> POST http://127.0.0.1:8000/api/chat/analyze
-> FastAPI backend
-> ai module
```

백엔드는 `http://127.0.0.1:5173`과 `http://localhost:5173` origin을 허용한다. 프론트엔드는 상대 경로 `/api/chat/analyze`가 아니라 `http://127.0.0.1:8000/api/chat/analyze`를 호출한다.

## 백엔드와 AI 코드 분리

기존 `app/api.py`의 책임을 나눈다.

```text
back/
├── api.py
└── run_local_demo.py

ai/
├── config.py
├── model/
├── agent_analysis/
├── notification/
└── schemas/
```

`back/api.py`는 FastAPI 앱, CORS, 요청 검증, 응답 조립을 맡는다. `ai/` 내부 모듈은 의미 분석, mock 모델 점수, Agent 결과 검증, 알림 포맷 생성을 맡는다.

백엔드는 위험 구간이나 사건을 의미적으로 판단하지 않는다. `warning` 이상일 때 `ai.agent_analysis`를 호출하고, 그 결과를 데이터 스키마에 맞게 프론트로 전달한다.

## AGENTS.md 변경 방향

루트 `AGENTS.md`는 다음 내용을 유지한다.

- Notion 기준 문서
- 작업 시작 규칙
- 개발 원칙
- 함수 작성 규칙
- 작업 기록 규칙

다음 내용은 새 디렉토리 기준으로 업데이트한다.

- 서비스 개요
- 해결하려는 문제
- 역할 분리
- 데이터 기준 문서

`AGENTS.md`에는 작업 시작 시 루트 `data_schema.md`를 반드시 읽고, 프론트엔드·백엔드·AI·알림의 입출력 판단 기준으로 삼는 규칙을 추가한다. `data_schema.md`와 코드 또는 phase 문서가 충돌하면 임의로 수정하지 않고 사용자에게 보고한다.

## README.md 교체 방향

기존 `README.md` 내용은 새 구조 기준으로 완전히 교체한다.

포함할 내용:

- 프로젝트 목적
- 현재 디렉토리 구조
- 백엔드 실행 방법
- 프론트엔드 실행 방법
- 브라우저 접속 위치
- 전체 테스트 실행 방법
- phase 문서와 테스트 결과 기록 위치
- legacy `Nvidia_test`의 보존 목적

## 테스트 방향

자동 테스트는 기존 phase 테스트를 새 import 경로와 CORS 구조에 맞게 갱신한다.

필수 검증:

- `front/` JavaScript가 `http://127.0.0.1:8000/api/chat/rooms`로 채팅방을 만든 뒤 `http://127.0.0.1:8000/api/chat/analyze`를 호출한다.
- `back/` FastAPI 앱이 `127.0.0.1:5173` origin에 CORS 헤더를 반환한다.
- `POST /api/chat/rooms`, `GET /api/chat/rooms`, `POST /api/chat/analyze` 계약은 루트 `data_schema.md`와 `docs/phase_*.md` 기준을 따른다.
- `warning` 이상에서 백엔드가 AI Agent 분석을 호출하고, 위험 구간과 관리자 알림을 응답에 포함한다.
- 전체 테스트 결과와 phase별 확인 결과는 `test/`에 남긴다.

## 보존과 제거 기준

`Nvidia_test`는 삭제하지 않고 `legacy/Nvidia_test/`로 이동해 보존한다. 새 실행 구조는 `front/`, `back/`, `ai/`만 사용한다.

`app/frontend`는 CORS 분리 구조에서는 사용하지 않는다. 필요한 정적 파일은 `front/`로 이동하고, `app/` 자체는 `back/`과 `ai/`로 책임을 나눈 뒤 제거한다.

`docs/superpowers`는 유지한다. 큰 구조 변경의 설계와 구현 계획은 여기에 기록한다.

## 실행 명령 목표

백엔드:

```bash
cd /Users/mac/Desktop/Team/silentguard
python3 -m back.run_local_demo
```

프론트엔드:

```bash
cd /Users/mac/Desktop/Team/silentguard
python3 -m http.server 5173 -d front
```

브라우저:

```text
http://127.0.0.1:5173
```

테스트:

```bash
cd /Users/mac/Desktop/Team/silentguard
python3 -m pytest test -q
node --check front/app.js
```

## 구현 전 확인 사항

이 설계는 사용자가 확정한 방향을 기준으로 작성했다. 구현 단계에서는 기존 실행 중인 로컬 서버를 종료한 뒤 파일 이동과 import 경로 변경을 진행해야 한다.
