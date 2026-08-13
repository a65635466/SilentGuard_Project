## 현재 사항

- `ai/legacy_app/demo.html`에 mock 요청 JSON과 Agent 응답 JSON을 보여주는 화면을 보존함.
- 현재 실행 서버는 `back/run_local_demo.py`와 `back/api.py`를 기준으로 동작함.
- `http://127.0.0.1:8000`에서 HTML과 mock 입력 표시까지 확인했고 테스트 8개가 통과함.
- 루트 `.env`를 `app/config.py`의 `load_dotenv()`로 자동 로드하도록 세팅함.
- `.env`의 API 키로 mock 요청을 보내 `risk_chat_segments`와 `missing_context` 실제 응답을 받음.
- `ai/agent_analysis/silentguard_agent.py`에 system prompt, user input, OpenAI 호출, 응답 검증을 담당하는 `SilentGuardAgent` 클래스를 분리함.
- `openai` Python SDK의 `OpenAI().responses.create()`로 실제 호출하고 응답을 재확인함.

## 문제/막힌 지점

- 없음.

## 결정된 사항

- 현재 실행 코드는 `back/`, `front/`, `ai/` 폴더 기준으로 관리함.
- API 키는 서버의 `OPENAI_API_KEY` 환경변수에서만 읽음.
- 모델은 `OPENAI_MODEL` 환경변수로 바꿀 수 있게 함.
- 브라우저에는 API 키를 보내지 않고 로컬 Python 서버만 OpenAI API를 호출함.
- 실제 키는 `.env`에 넣되 Git에 올라가지 않도록 `.gitignore`에 등록함.
- API 호출과 Agent 책임은 `SilentGuardAgent`가 맡고, 로컬 서버는 Agent를 호출만 함.
