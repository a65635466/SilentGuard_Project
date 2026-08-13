"""Load local environment variables for the SilentGuard demo."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# OpenAI 환경변수의 앞뒤 공백과 줄바꿈을 제거한다.
def normalize_environment_values() -> None:
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"):
        value = os.getenv(name)
        if value is not None:
            os.environ[name] = value.strip()


normalize_environment_values()
