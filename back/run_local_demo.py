"""Start the local SilentGuard backend server."""

import uvicorn


# CORS로 분리된 FastAPI 백엔드 앱을 로컬 서버로 실행한다.
def run() -> None:
    uvicorn.run("back.api:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
