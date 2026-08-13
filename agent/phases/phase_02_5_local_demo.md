# Phase 2.5: 로컬 요청·응답 확인 화면

## 목표

mock 대화를 OpenAI Agent에 보내고, 요청과 응답을 간단한 로컬 HTML에서 확인한다.

## 해야 할 일

- [x] `ai/agent_analysis/`의 Agent 코드를 로컬 백엔드 서버에서 호출한다.
- [x] mock 입력 JSON을 브라우저에 표시한다.
- [x] 버튼을 누르면 로컬 서버가 OpenAI API를 호출하게 한다.
- [x] API 응답 JSON을 브라우저에 표시한다.
- [x] `OPENAI_API_KEY`를 브라우저에 노출하지 않는다.
- [x] `OPENAI_MODEL` 환경변수로 모델을 변경할 수 있게 한다.
- [x] 로컬 주소로 접속해 HTML과 mock 요청 흐름을 확인한다.
- [x] API 키가 전달된 프로세스에서 실제 OpenAI 응답을 확인한다.
- [x] 명확한 `SilentGuardAgent` 실행 주체를 분리한다.

## 실행 방법

```bash
cd /Users/mac/Desktop/Team/silentguard
export OPENAI_API_KEY='직접 입력'
export OPENAI_MODEL='gpt-4o-mini'
python3 -m back.run_local_demo
```

또는 루트 `.env`에 값을 넣고 `python-dotenv`를 설치하면 서버가 자동으로 읽는다.

브라우저에서 `http://127.0.0.1:8000`을 연다.

## 입력과 출력

- 입력: `ai/legacy_app/sample_input.json` 또는 프론트엔드가 전송하는 메시지 JSON
- 출력: Phase 2의 `risk_chat_segments`, `missing_context`

## 변경 파일

- `ai/legacy_app/demo.html`
- `back/run_local_demo.py`
- `back/api.py`
- `ai/config.py`
- `ai/agent_analysis/silentguard_agent.py`
- `.env.example`
- `requirements.txt`

## 검증 방법

- 서버 실행 후 `/`에서 HTML이 열리는지 확인한다.
- `분석 실행` 버튼으로 요청 JSON과 응답 JSON이 표시되는지 확인한다.

## 작업 결과

HTML, mock 입력 화면, 실제 OpenAI 위험 구간 응답을 모두 확인했다.

## 남은 문제

없음.
