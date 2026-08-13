import os

from ai import config


def test_normalize_environment_values_strips_openai_values(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key\n")
    monkeypatch.setenv("OPENAI_MODEL", " gpt-4o-mini\n")
    monkeypatch.setenv("OPENAI_BASE_URL", " https://api.openai.com/v1\n")

    config.normalize_environment_values()

    assert os.environ["OPENAI_API_KEY"] == "sk-test-key"
    assert os.environ["OPENAI_MODEL"] == "gpt-4o-mini"
    assert os.environ["OPENAI_BASE_URL"] == "https://api.openai.com/v1"
