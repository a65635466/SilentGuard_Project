import unittest
from unittest.mock import patch

from app.notion_delivery import build_notion_create_page_body, create_notion_report_page, extract_notion_page_url, load_notion_config
from app.risk_segments import AgentError
from app.test_notion_markdown import incident, payload


class NotionDeliveryTests(unittest.TestCase):
    def test_loads_notion_config(self):
        with patch.dict("os.environ", {"NOTION_TOKEN": "secret", "NOTION_PARENT_PAGE_ID": "page_001", "NOTION_VERSION": "2026-03-11"}):
            result = load_notion_config()
        self.assertEqual(result["parent_page_id"], "page_001")
        self.assertEqual(result["notion_version"], "2026-03-11")

    def test_requires_notion_token(self):
        with patch.dict("os.environ", {"NOTION_TOKEN": "", "NOTION_PARENT_PAGE_ID": "page_001"}):
            with self.assertRaisesRegex(AgentError, "NOTION_TOKEN"):
                load_notion_config()

    def test_builds_create_page_body(self):
        body = build_notion_create_page_body(payload(), incident(), "parent_001")
        self.assertEqual(body["parent"]["page_id"], "parent_001")
        self.assertIn("SilentGuard 위험 신호 알림", body["properties"]["title"]["title"][0]["text"]["content"])
        self.assertIn("## 1. 요약", body["markdown"])
        self.assertNotIn("# SilentGuard 위험 신호 알림", body["markdown"])

    def test_extracts_notion_url(self):
        self.assertEqual(extract_notion_page_url({"url": "https://notion.so/test"}), "https://notion.so/test")

    def test_rejects_missing_notion_url(self):
        with self.assertRaisesRegex(AgentError, "page url"):
            extract_notion_page_url({})

    def test_create_report_page_returns_url(self):
        fake_response = {"id": "page_001", "url": "https://notion.so/page_001"}
        with patch.dict("os.environ", {"NOTION_TOKEN": "secret", "NOTION_PARENT_PAGE_ID": "parent_001"}):
            with patch("app.notion_delivery.post_notion_page", return_value=fake_response):
                result = create_notion_report_page(payload(), incident())
        self.assertTrue(result["ok"])
        self.assertEqual(result["notion_url"], "https://notion.so/page_001")


if __name__ == "__main__":
    unittest.main()
