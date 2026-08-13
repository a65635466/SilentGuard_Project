# SilentGuard

SilentGuard는 채팅 대화에서 사이버 괴롭힘 위험 신호를 조기에 감지하고, 관리자가 원본 대화와 근거를 함께 확인할 수 있도록 정리해주는 로컬 MVP 프로젝트입니다.

이 프로젝트는 학교폭력, 가해자, 피해자를 확정 판정하지 않습니다. 모델과 Agent는 위험 가능성을 알려주고, 최종 판단은 관리자가 원본 대화와 근거를 보고 하도록 돕는 데 목적이 있습니다.

## 주요 기능

- 채팅방 생성 및 메시지 입력
- mock 모델 또는 모델 런타임을 통한 `bullying_probability` 계산
- 백엔드에서 `normal`, `caution`, `warning`, `immediate` 위험 단계 계산
- `warning` 이상일 때 Agent 분석 실행
- 위험 구간, 사건 요약, 근거 메시지 ID, 관리자용 알림 내용 생성
- 프론트엔드에서 원본 대화, 위험 확률, 위험 단계, Agent 결과, 알림 전달 상태 표시
- 실제 외부 전송 없이도 MVP 알림 상태 확인 가능

## 프로젝트 구조

```text
front/              브라우저 화면과 사용자 입력 UI
back/               FastAPI 백엔드 API
ai/model/           위험 확률 계산 모델 또는 mock 모델
ai/agent_analysis/  위험 구간과 사건 분석 Agent
ai/notification/    관리자 알림 내용과 전달 상태 처리
ai/schemas/         공통 데이터 계약
agent/              Agent 담당 Phase 문서
docs/               전체 연결 Phase 문서
test/               자동 테스트와 Phase별 테스트 결과
model/              실제 모델 학습/평가 관련 코드와 데이터 처리
```

## 데이터 흐름

```text
front
-> back API
-> ai/model 위험 확률 계산
-> back 위험 단계 계산
-> warning 이상이면 ai/agent_analysis 실행
-> ai/notification 알림 결과 생성
-> back 응답 조립
-> front 결과 표시
```

위험 단계 기준은 다음과 같습니다.

```text
0.00 <= probability < 0.50 = normal
0.50 <= probability < 0.70 = caution
0.70 <= probability < 0.85 = warning
0.85 <= probability <= 1.00 = immediate
```

## 실행 방법

### 1. 의존성 설치

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. 백엔드 실행

```bash
python -m uvicorn back.api:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 프론트엔드 실행

다른 터미널에서 실행합니다.

```bash
python -m http.server 5173 -d front
```

브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:5173
```

## 테스트

```bash
python -m pytest
```

현재 MVP 기준 테스트는 프론트엔드-백엔드-모델-Agent-알림 연결 흐름을 확인합니다.

## GitHub에 포함하지 않은 파일

다음 파일과 폴더는 크기 또는 보안 문제로 GitHub에 올리지 않습니다.

- `.env`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- `ai/model/embedders/`
- `ai/model/artifacts/`

실제 임베더와 모델 아티팩트가 필요한 경우 별도로 받아서 같은 경로에 배치해야 합니다. 기본 MVP 흐름은 mock 모델 중심으로 확인할 수 있습니다.

## 주의사항

- 실제 사용자 개인정보가 포함된 데이터를 사용하지 않습니다.
- Agent 결과는 자동 분석 참고자료이며 최종 판단이 아닙니다.
- 백엔드는 위험 구간과 사건을 직접 판단하지 않고, 해당 분석은 Agent가 담당합니다.
- 첫 MVP는 로컬 실행을 기준으로 하며 서버 배포, 운영 DB, 실제 법적 신고 자동화는 포함하지 않습니다.
