import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.notion_markdown import build_notion_markdown, escape_table_cell, save_notion_markdown_report


def payload():
    return {
        "analysis_id": "analysis_001",
        "room_id": "room_001",
        "bullying_probability": 0.91,
        "risk_level": "immediate",
        "messages": [
            {
                "message_id": "msg_001",
                "sender_label": "A",
                "text": "너 왜 또 여기 들어왔냐",
                "created_at": "2026-08-08T14:28:00+09:00",
            },
            {
                "message_id": "msg_002",
                "sender_label": "B",
                "text": "그냥 나가라",
                "created_at": "2026-08-08T14:28:20+09:00",
            },
        ],
    }


def incident():
    return {
        "incident_id": "incident_001",
        "risk_chat_segments": [
            {
                "segment_id": "segment_001",
                "start_message_id": "msg_001",
                "end_message_id": "msg_002",
                "evidence_message_ids": ["msg_001", "msg_002"],
                "start_at": "2026-08-08T14:28:00+09:00",
                "end_at": "2026-08-08T14:28:20+09:00",
                "reason": "배제 표현이 이어집니다.",
            }
        ],
        "suspected_risk_types": [{"type": "배제성", "evidence_message_ids": ["msg_001", "msg_002"]}],
        "context_reason": "배제와 압박의 위험 신호로 볼 수 있습니다.",
        "evidence_message_ids": ["msg_001", "msg_002"],
        "manager_summary": "원본 앞뒤 대화 확인이 필요합니다.",
        "missing_context": ["대화 이전 상황은 확인하지 못했습니다."],
        "recommended_initial_actions": ["원본 메시지를 보존합니다."],
        "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
    }


class NotionMarkdownTests(unittest.TestCase):
    def test_builds_report_sections(self):
        markdown = build_notion_markdown(payload(), incident())
        self.assertIn("# SilentGuard 위험 신호 알림", markdown)
        self.assertIn("## 4. 감지된 위험 유형", markdown)
        self.assertIn("## 6. 주요 근거 메시지", markdown)
        self.assertIn("msg_001", markdown)
        self.assertIn("너 왜 또 여기 들어왔냐", markdown)
        self.assertIn("자동 분석된 위험 신호이며 최종 판단이 아닙니다.", markdown)

    def test_escapes_markdown_table_cell(self):
        self.assertEqual(escape_table_cell("a|b\nc"), "a\\|b<br>c")

    def test_saves_report_file(self):
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            saved_path = save_notion_markdown_report("hello", output_path)
            self.assertEqual(saved_path, output_path)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "hello")


if __name__ == "__main__":
    unittest.main()
