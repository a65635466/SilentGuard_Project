# SilentGuard 실행

## 1. 의존성 설치

실제 모델과 백엔드를 같은 Python 프로세스에서 실행하므로 `silentguard-model` 환경을 사용한다.

```bash
cd /Users/mac/Desktop/Team/silentguard
source /Users/mac/venvs/silentguard-model/bin/activate
python -m pip install -r requirements.txt
```

## 2. 백엔드 실행

터미널을 새로 열 때마다 아래 명령을 실행한다.

```bash
cd /Users/mac/Desktop/Team/silentguard
source /Users/mac/venvs/silentguard-model/bin/activate
python -m uvicorn back.api:app --host 127.0.0.1 --port 8000 --reload
```

## 3. 프론트엔드 실행

백엔드와 다른 터미널에서 실행한다.

```bash
cd /Users/mac/Desktop/Team/silentguard
python3 -m http.server 5173 -d front
```

브라우저에서 `http://127.0.0.1:5173`을 연다.

## 4. 모델 단독 확인

```bash
cd /Users/mac/Desktop/Team/silentguard
source /Users/mac/venvs/silentguard-model/bin/activate
python -m ai.model.predict
```

## 5. 서버 종료

```bash
lsof -tiTCP:8000 -sTCP:LISTEN | xargs kill
```

```bash
lsof -tiTCP:5173 -sTCP:LISTEN | xargs kill
```
