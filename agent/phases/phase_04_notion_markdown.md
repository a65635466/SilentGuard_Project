# Phase 04: Notion Markdown 보고서 생성

## 목표

Agent 분석 결과와 원본 메시지를 Notion에 넣을 수 있는 Markdown 보고서로 만든다.

## 참고 문서

- 팀 공통 `AGENTS.md`
- `agent/AGENTS.md`
- `agent/overview.md`
- `agent/PHASE_DOCUMENT_RULES.md`

## 해야 할 일

- [x] Agent 분석 결과 샘플을 현재 AI/알림 구조 기준으로 관리한다.
- [x] Agent 분석 결과와 원본 메시지를 받아 Markdown 문자열을 만드는 함수를 작성한다.
- [x] 요약, 위험 유형, 위험 구간, 근거 메시지, 추가 확인, 초기 조치, 주의 문구 섹션을 만든다.
- [x] Markdown 보고서를 로컬 파일로 저장하는 실행 파일을 만든다.
- [x] 테스트로 주요 섹션과 근거 메시지 출력 여부를 확인한다.

## 입력과 출력

입력:

```text
ai/legacy_app/sample_input.json
ai/legacy_app/sample_incident_result.json
```

출력:

```text
ai/legacy_app/output/notion_report.md
```

## 변경 파일

- `ai/notification/notion_markdown.py`
- `ai/legacy_app/run_phase_04.py`
- `ai/legacy_app/sample_incident_result.json`
- `ai/legacy_app/test_notion_markdown.py`
- `agent/phases/phase_04_notion_markdown.md`
- `agent/phases/phase_04_status.md`

## 검증 방법

```bash
python3 -m pytest test -q
```

## 작업 결과

Agent 분석 결과와 원본 메시지를 합쳐 Notion용 Markdown 보고서를 생성하도록 구현했다.

현재 전체 테스트 17개가 통과했다.

추가로 Codex 세션의 Notion MCP 도구를 사용해 실제 Notion 테스트 페이지 생성도 확인했다.

## 남은 문제

없음

## 다음 Phase로 넘길 내용

다음 Phase에서는 로컬 Python 실행만으로 Notion 페이지를 만들 수 있게 연결 방식을 정해야 한다.

현재 서비스 경로는 `ai/notification/notion_markdown.py`의 Markdown 생성 함수와 `ai/notification/notion_delivery.py`의 Notion HTTP 생성 함수를 사용한다. 실제 Notion 페이지 생성은 Codex 세션의 Notion MCP 도구와 HTTP API 경로로 별도 확인했다.
