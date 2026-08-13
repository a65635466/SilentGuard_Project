import unittest
from unittest.mock import patch
from types import SimpleNamespace

from app.risk_segments import AgentError, validate_segments
from app.silentguard_agent import SilentGuardAgent


def payload():
    return {
        "analysis_id": "analysis_001",
        "room_id": "room_001",
        "bullying_probability": 0.91,
        "risk_level": "immediate",
        "messages": [
            {
                "message_id": "msg_001",
                "sender_id": "A",
                "sender_label": "A",
                "text": "너 왜 또 여기 들어왔냐",
                "created_at": "2026-08-08T14:28:00+09:00",
            },
            {
                "message_id": "msg_002",
                "sender_id": "B",
                "sender_label": "B",
                "text": "그냥 나가라",
                "created_at": "2026-08-08T14:28:20+09:00",
            },
        ],
    }


class FakeResponses:
    def create(self, **kwargs):
        assert kwargs["instructions"]
        assert kwargs["text"]["format"]["type"] == "json_schema"
        if kwargs["text"]["format"]["name"] == "silentguard_incident_notification":
            return SimpleNamespace(output_text='{"incident_id":"inc_001","risk_chat_segments":[{"segment_id":"seg_001","start_message_id":"msg_001","end_message_id":"msg_002","evidence_message_ids":["msg_001","msg_002"],"start_at":"2026-08-08T14:28:00+09:00","end_at":"2026-08-08T14:28:20+09:00","reason":"같은 대화 흐름에서 배제 신호가 이어집니다."}],"suspected_risk_types":[{"type":"배제성","evidence_message_ids":["msg_001","msg_002"]}],"context_reason":"배제 표현이 이어져 추가 확인이 필요합니다.","evidence_message_ids":["msg_001","msg_002"],"manager_summary":"14:28경 대화에서 배제 표현이 이어졌습니다. 원본 전후 대화와 당사자 상황을 추가 확인해야 합니다.","missing_context":["대화 이전 상황은 확인하지 못했습니다."],"recommended_initial_actions":["원본과 앞뒤 대화를 함께 확인합니다."],"disclaimer":"자동 분석된 위험 신호이며 최종 판단이 아닙니다."}')
        return SimpleNamespace(output_text='{"risk_chat_segments":[{"segment_id":"seg_001","start_message_id":"msg_001","end_message_id":"msg_002","evidence_message_ids":["msg_001","msg_002"],"start_at":"2026-08-08T14:28:00+09:00","end_at":"2026-08-08T14:28:20+09:00","reason":"같은 대화 흐름에서 배제 표현이 이어집니다."}],"missing_context":[]}')


class FakeClient:
    responses = FakeResponses()


class RiskSegmentTests(unittest.TestCase):
    def test_calls_model_and_validates_ids(self):
        result = SilentGuardAgent(client=FakeClient(), model="test-model").analyze(payload())
        self.assertEqual(result["risk_chat_segments"][0]["evidence_message_ids"], ["msg_001", "msg_002"])

    def test_rejects_unknown_evidence_id(self):
        result = {
            "risk_chat_segments": [{
                "segment_id": "seg_001",
                "start_message_id": "msg_001",
                "end_message_id": "msg_002",
                "evidence_message_ids": ["msg_missing"],
                "start_at": "2026-08-08T14:28:00+09:00",
                "end_at": "2026-08-08T14:28:20+09:00",
                "reason": "근거",
            }],
            "missing_context": [],
        }
        with self.assertRaises(AgentError):
            validate_segments(result, payload()["messages"])

    def test_requires_api_key_before_call(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(AgentError, "OPENAI_API_KEY"):
                SilentGuardAgent()

    def test_builds_incident_notification(self):
        result = SilentGuardAgent(client=FakeClient(), model="test-model").analyze_incident(payload())
        self.assertEqual(result["incident_id"], "inc_001")
        self.assertEqual(result["suspected_risk_types"][0]["type"], "배제성")


if __name__ == "__main__":
    unittest.main()
