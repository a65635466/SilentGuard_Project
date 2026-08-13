## 현재 사항

- Phase 1 입력 계약 검증 코드를 작성함.
- 샘플 JSON을 CLI로 읽어 `VALID` 또는 `INVALID`를 출력함.
- 필수 필드, 확률 범위, 위험 단계, 메시지 필드, ISO-8601 시간, 중복 메시지 ID를 검증함.

## 문제/막힌 지점

- 없음. 실제 LLM 분석 호출은 Phase 2 구현 범위임.

## 결정된 사항

- 구현 파일은 루트 `app/` 폴더의 `contract.py`, `run_phase_01.py`, `test_contract.py`로 둠.
- Phase 1에서는 의미 판단이나 사건 생성을 하지 않고 입력만 검증함.
