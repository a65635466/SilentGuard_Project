## 현재 사항

- `build_notion_markdown`: Agent 분석 결과와 원본 메시지를 받아 Notion용 Markdown 보고서를 만든다.
- `build_summary_section`: 위험 단계, 위험 확률, 분석 ID, 사건 ID를 요약 섹션으로 만든다.
- `build_risk_types_table`: 의심 위험 유형과 근거 메시지 ID를 표로 만든다.
- `build_risk_segments_table`: 위험 구간의 시간, 이유, 근거 메시지를 표로 만든다.
- `build_evidence_messages_table`: 근거 메시지 원문을 표로 만든다.
- `save_notion_markdown_report`: 생성된 Markdown을 로컬 파일로 저장한다.
- `run_phase_04`: 샘플 입력과 샘플 Agent 결과로 Notion 보고서 Markdown을 생성한다.
- 전체 테스트 17개가 통과했다.
- Codex 세션의 Notion MCP 도구로 실제 Notion 테스트 페이지 생성을 확인했다.

## 문제/막힌 지점

- 로컬 Python 명령은 아직 Notion MCP를 직접 호출하지 못한다.
- 사용자가 터미널에서 실행한 에러 내용은 아직 확인하지 못했다.

## 결정된 사항

- Gmail/Naver에는 상세 내용을 넣지 않고 Notion 링크만 보내는 구조로 둔다.
- 실제 알림 본문은 Notion Markdown 보고서가 담당한다.
- Phase 4에서는 실제 Notion MCP 연결 없이 로컬 Markdown 파일 생성까지만 구현한다.
- 로컬 명령으로 Notion까지 보내는 작업은 다음 Phase에서 별도로 구현한다.
