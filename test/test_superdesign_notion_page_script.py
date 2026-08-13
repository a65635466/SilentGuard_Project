import importlib
import json
from pathlib import Path


# Superdesign Notion 스크립트가 lowercase .env 키를 읽는지 확인한다.
def test_load_notion_config_uses_requested_lowercase_env_keys(tmp_path, monkeypatch) -> None:
    module = importlib.import_module("scripts.create_superdesign_notion_page")
    env_path = tmp_path / ".env"
    env_path.write_text(
        "notion_api_key=secret_test\nnotion_parent_id=parent_test\nnotion_version=2022-06-28\n",
        encoding="utf-8",
    )

    config = module.load_notion_config(env_path)

    assert config == {
        "token": "secret_test",
        "parent_id": "parent_test",
        "notion_version": "2022-06-28",
    }


# Superdesign Notion 스크립트가 기존 대문자 Notion env 키도 fallback으로 읽는지 확인한다.
def test_load_notion_config_falls_back_to_existing_uppercase_env_keys(tmp_path) -> None:
    module = importlib.import_module("scripts.create_superdesign_notion_page")
    env_path = tmp_path / ".env"
    env_path.write_text(
        "NOTION_TOKEN=secret_existing\nNOTION_PARENT_PAGE_ID=parent_existing\nNOTION_VERSION=2026-03-11\n",
        encoding="utf-8",
    )

    config = module.load_notion_config(env_path)

    assert config == {
        "token": "secret_existing",
        "parent_id": "parent_existing",
        "notion_version": "2026-03-11",
    }


# Superdesign 디자인 기준으로 Notion native block payload를 만드는지 확인한다.
def test_build_superdesign_notion_page_body_uses_report_mockup(tmp_path) -> None:
    module = importlib.import_module("scripts.create_superdesign_notion_page")
    design_path = tmp_path / "design-system.md"
    design_path.write_text(
        "# REDPLAG Notion Report Design System\n"
        "- Title: `REDPLAG` and `[위험 신호 알림]`\n"
        "- Tone: serious, calm, administrative, evidence-first.\n",
        encoding="utf-8",
    )

    body = module.build_superdesign_notion_page_body(design_path, "parent_test")

    assert body["parent"] == {"type": "page_id", "page_id": "parent_test"}
    assert body["properties"]["title"]["title"][0]["text"]["content"] == "REDPLAG [위험 신호 알림]"
    assert "children" in body
    assert "markdown" not in body

    serialized = json.dumps(body, ensure_ascii=False)
    assert "1. 탐지 개요" in serialized
    assert "3. 감지된 위험 유형" in serialized
    assert "4. 위험 구간 로그" in serialized
    assert "5. 주요 근거 메시지" in serialized
    assert "6. 추천 조치" in serialized
    assert "자동 분석된 위험 신호이며 최종 판단이 아닙니다." in serialized


# Notion API 전송 함수가 토큰과 부모 페이지 body를 사용해 URL을 반환하는지 확인한다.
def test_create_superdesign_notion_page_posts_body_with_auth(tmp_path) -> None:
    module = importlib.import_module("scripts.create_superdesign_notion_page")
    design_path = tmp_path / "design-system.md"
    design_path.write_text("# REDPLAG Notion Report Design System\n", encoding="utf-8")
    sent = {}

    def fake_urlopen(request, timeout):
        sent["timeout"] = timeout
        sent["url"] = request.full_url
        sent["headers"] = dict(request.header_items())
        sent["body"] = json.loads(request.data.decode("utf-8"))

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps({"id": "page_001", "url": "https://notion.so/page_001"}).encode("utf-8")

        return FakeResponse()

    result = module.create_superdesign_notion_page(
        design_path,
        {"token": "secret_test", "parent_id": "parent_test", "notion_version": "2022-06-28"},
        opener=fake_urlopen,
    )

    assert result == {"page_id": "page_001", "url": "https://notion.so/page_001"}
    assert sent["url"] == "https://api.notion.com/v1/pages"
    headers = {key.lower(): value for key, value in sent["headers"].items()}
    assert headers["authorization"] == "Bearer secret_test"
    assert headers["notion-version"] == "2022-06-28"
    assert sent["body"]["parent"]["page_id"] == "parent_test"
