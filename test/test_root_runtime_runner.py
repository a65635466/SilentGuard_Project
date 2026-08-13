from back import run_local_demo


# 루트 실행기가 CORS용 백엔드 FastAPI 앱을 실행하는지 확인한다.
def test_root_runtime_runner_starts_backend_fastapi_app(monkeypatch) -> None:
    received_arguments = {}

    def fake_run(app, host: str, port: int) -> None:
        received_arguments.update({"app": app, "host": host, "port": port})

    monkeypatch.setattr(run_local_demo.uvicorn, "run", fake_run)

    run_local_demo.run()

    assert received_arguments == {
        "app": "back.api:app",
        "host": "127.0.0.1",
        "port": 8000,
    }
