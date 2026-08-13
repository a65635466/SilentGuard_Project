# OpenAI 설정 정규화 확인 결과

- 원인: `.env`의 `OPENAI_API_KEY` 값 끝 줄바꿈이 Authorization 헤더를 깨뜨려 Agent 호출이 실패했다.
- 수정: `ai.config.normalize_environment_values`가 `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`의 앞뒤 공백과 줄바꿈을 제거한다.
- 자동 검증: `test/test_openai_config.py` 통과
- 전체 검증: `python3 -m pytest test -q` 결과 17개 통과
- 외부 내용 전송 없는 확인: OpenAI `models.list()` 호출에서 헤더 정규화 확인
