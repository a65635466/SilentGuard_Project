import pytest


# 자동화 테스트는 실제 대형 모델을 로딩하지 않고 API 계약만 검증한다.
@pytest.fixture(autouse=True)
def use_mock_model_for_api_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SILENTGUARD_MODEL_PROVIDER", "mock")
