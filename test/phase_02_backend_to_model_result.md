# Phase 02 실행 결과

- 검증 대상: 백엔드에서 mock 모델로 전달하는 시간순 원본 메시지 묶음
- 자동 검증: `test_phase_02_sorts_messages_before_mock_model_scoring` 통과
- 실행 경로: `back/api.py`가 `ai/model/mock_model.py`를 호출한다.
- 결과: 입력 순서와 무관하게 `created_at` 기준으로 정렬한 메시지 묶음을 mock 점수 계산에 사용한다.
