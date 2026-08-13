import unittest

from app.contract import ContractError, validate_agent_input


def valid_payload():
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
                "text": "원문 메시지",
                "created_at": "2026-08-08T14:28:00+09:00",
            }
        ],
    }


class AgentInputContractTests(unittest.TestCase):
    def test_accepts_agreed_payload(self):
        result = validate_agent_input(valid_payload())
        self.assertEqual(result["analysis_id"], "analysis_001")
        self.assertEqual(result["messages"][0]["message_id"], "msg_001")

    def test_rejects_probability_outside_range(self):
        payload = valid_payload()
        payload["bullying_probability"] = 1.1
        with self.assertRaises(ContractError):
            validate_agent_input(payload)

    def test_rejects_unknown_risk_level(self):
        payload = valid_payload()
        payload["risk_level"] = "critical"
        with self.assertRaises(ContractError):
            validate_agent_input(payload)

    def test_rejects_duplicate_message_ids(self):
        payload = valid_payload()
        payload["messages"].append(dict(payload["messages"][0]))
        with self.assertRaises(ContractError):
            validate_agent_input(payload)

    def test_rejects_invalid_timestamp(self):
        payload = valid_payload()
        payload["messages"][0]["created_at"] = "not-a-date"
        with self.assertRaises(ContractError):
            validate_agent_input(payload)


if __name__ == "__main__":
    unittest.main()
