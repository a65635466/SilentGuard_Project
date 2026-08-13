from fastapi.testclient import TestClient

from back import api as api_module


# Phase 통합 테스트용 채팅방을 만든다.
def create_test_room(client: TestClient, room_name: str = "상담 확인 방") -> dict:
    response = client.post(
        "/api/chat/rooms",
        json={"room_name": room_name, "notification_email": "teacher@example.com"},
    )

    assert response.status_code == 200
    return response.json()


# Phase 테스트에 쓰는 원본 메시지를 만든다.
def build_immediate_messages() -> list[dict]:
    texts = [
        ("A", "너 왜 또 여기 들어왔냐"),
        ("B", "그냥 얘기하려고"),
        ("A", "아무도 너랑 말하기 싫대"),
        ("C", "맞아 그냥 나가"),
    ]
    return [
        {
            "message_id": f"msg_{index:03d}",
            "sender_id": sender_id,
            "sender_label": sender_id,
            "text": text,
            "created_at": f"2026-08-08T14:{27 + index:02d}:00+09:00",
        }
        for index, (sender_id, text) in enumerate(texts, start=1)
    ]


# Phase 04와 05에서 Agent 입력과 반환이 문서의 역할 경계를 지키는지 확인한다.
def test_phase_04_and_05_pass_agent_incident_to_backend(monkeypatch) -> None:
    received_payloads = []

    def fake_agent(payload: dict) -> dict:
        received_payloads.append(payload)
        incident = {
            "incident_id": "incident_demo_room_001",
            "risk_chat_segments": [
                {
                    "segment_id": "seg_001",
                    "start_message_id": "msg_001",
                    "end_message_id": "msg_004",
                    "evidence_message_ids": ["msg_001", "msg_003", "msg_004"],
                    "start_at": "2026-08-08T14:28:00+09:00",
                    "end_at": "2026-08-08T14:31:00+09:00",
                    "reason": "배제와 압박의 위험 신호가 이어져 추가 확인이 필요합니다.",
                }
            ],
            "suspected_risk_types": [
                {"type": "배제성", "evidence_message_ids": ["msg_003", "msg_004"]}
            ],
            "context_reason": "특정 사용자를 향한 배제 표현이 반복됩니다.",
            "evidence_message_ids": ["msg_001", "msg_003", "msg_004"],
            "manager_summary": "원본 대화에서 배제와 압박의 위험 신호가 보입니다.",
            "missing_context": ["이전 대화 확인이 필요합니다."],
            "recommended_initial_actions": ["원본 메시지를 보존합니다."],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        }
        return {
            "status": "completed",
            "summary": incident["manager_summary"],
            "incident": incident,
            "risk_segments": incident["risk_chat_segments"],
        }

    monkeypatch.setattr(api_module, "request_agent_analysis", fake_agent)
    client = TestClient(api_module.app)
    room = create_test_room(client)
    response = TestClient(api_module.app).post(
        "/api/chat/analyze",
        json={"room_id": room["room_id"], "messages": build_immediate_messages()},
    )

    assert response.status_code == 200
    assert received_payloads[0].keys() == {
        "analysis_id",
        "room_id",
        "bullying_probability",
        "risk_level",
        "messages",
    }
    assert received_payloads[0]["room_id"] == room["room_id"]
    result = response.json()
    assert result["incident"]["incident_id"] == "incident_demo_room_001"
    assert result["risk_segments"][0]["segment_id"] == "seg_001"
    assert result["agent_response"]["summary"] == "원본 대화에서 배제와 압박의 위험 신호가 보입니다."


# Phase 06에서 Agent가 원본에 없는 근거 ID를 반환하면 알림을 보내지 않는지 확인한다.
def test_phase_06_skips_notification_when_agent_references_unknown_message_id(monkeypatch) -> None:
    notification_calls = []

    def fake_agent(_: dict) -> dict:
        return {
            "status": "completed",
            "summary": "입력에 없는 근거가 포함되어 있습니다.",
            "incident": {
                "incident_id": "incident_demo_room_002",
                "evidence_message_ids": ["msg_999"],
                "risk_chat_segments": [],
            },
            "risk_segments": [],
        }

    def fake_notification(_: dict) -> dict:
        notification_calls.append("sent")
        return {"channel": "unexpected"}

    monkeypatch.setattr(api_module, "request_agent_analysis", fake_agent)
    monkeypatch.setattr(api_module, "send_notification", fake_notification)
    client = TestClient(api_module.app)
    room = create_test_room(client)
    response = client.post(
        "/api/chat/analyze",
        json={"room_id": room["room_id"], "messages": build_immediate_messages()},
    )

    assert response.status_code == 200
    assert response.json()["notification_delivery"] == {
        "channel": "none",
        "status": "skipped_invalid_message_id",
        "sent_at": None,
        "external_message_id": None,
        "recipient_email": "teacher@example.com",
    }
    assert notification_calls == []


# Phase 08에서 Notion 링크 이메일 발송 성공을 프론트 응답용 전달 상태로 바꾸는지 확인한다.
def test_phase_08_send_notification_returns_sent_email_delivery(monkeypatch) -> None:
    received_notion_payloads = []
    received_email_payloads = []

    def fake_create_notion_report_page(payload: dict, incident: dict) -> dict:
        received_notion_payloads.append({"payload": payload, "incident": incident})
        return {
            "ok": True,
            "title": "SilentGuard 위험 신호 알림 - incident_demo_room_001",
            "notion_url": "https://notion.so/page_001",
            "notion_page_id": "page_001",
        }

    def fake_send_notion_email(payload: dict, notion_result: dict) -> dict:
        received_email_payloads.append({"payload": payload, "notion_result": notion_result})
        return {
            "channel": "email",
            "status": "sent",
            "recipient_email": payload["notification_email"],
            "sent_at": "2026-08-12T14:30:05+09:00",
            "external_message_id": "smtp-message-001",
        }

    monkeypatch.setattr(api_module, "create_notion_report_page", fake_create_notion_report_page)
    monkeypatch.setattr(api_module, "send_notion_link_email", fake_send_notion_email)

    payload = {
        "analysis_id": "analysis_demo_room_001",
        "room_id": "demo_room",
        "room_name": "상담 확인 방",
        "notification_email": "teacher@example.com",
        "messages": build_immediate_messages(),
        "bullying_probability": 0.91,
        "risk_level": "immediate",
        "incident": {
            "incident_id": "incident_demo_room_001",
            "risk_chat_segments": [],
            "suspected_risk_types": [],
            "context_reason": "배제 위험 신호가 있습니다.",
            "evidence_message_ids": ["msg_001"],
            "manager_summary": "관리자 확인이 필요합니다.",
            "missing_context": [],
            "recommended_initial_actions": [],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        },
    }

    result = api_module.send_notification(payload)

    assert received_notion_payloads == [{"payload": payload, "incident": payload["incident"]}]
    assert received_email_payloads == [
        {
            "payload": payload,
            "notion_result": {
                "ok": True,
                "title": "SilentGuard 위험 신호 알림 - incident_demo_room_001",
                "notion_url": "https://notion.so/page_001",
                "notion_page_id": "page_001",
            },
        }
    ]
    assert result["channel"] == "email"
    assert result["status"] == "sent"
    assert result["external_message_id"] == "smtp-message-001"
    assert result["notion_url"] == "https://notion.so/page_001"
    assert result["recipient_email"] == "teacher@example.com"
    assert result["sent_at"] == "2026-08-12T14:30:05+09:00"
    assert result["notion_page_id"] == "page_001"


# Phase 08에서 이메일 전달 결과가 API 응답의 notification_delivery로 내려가는지 확인한다.
def test_phase_08_api_response_includes_sent_email_delivery(monkeypatch) -> None:
    def fake_agent(_: dict) -> dict:
        incident = {
            "incident_id": "incident_demo_room_001",
            "risk_chat_segments": [
                {
                    "segment_id": "seg_001",
                    "start_message_id": "msg_001",
                    "end_message_id": "msg_004",
                    "evidence_message_ids": ["msg_001", "msg_003", "msg_004"],
                    "start_at": "2026-08-08T14:28:00+09:00",
                    "end_at": "2026-08-08T14:31:00+09:00",
                    "reason": "배제와 압박의 위험 신호가 이어져 추가 확인이 필요합니다.",
                }
            ],
            "suspected_risk_types": [
                {"type": "배제성", "evidence_message_ids": ["msg_003", "msg_004"]}
            ],
            "context_reason": "특정 사용자를 향한 배제 표현이 반복됩니다.",
            "evidence_message_ids": ["msg_001", "msg_003", "msg_004"],
            "manager_summary": "원본 대화에서 배제와 압박의 위험 신호가 보입니다.",
            "missing_context": ["이전 대화 확인이 필요합니다."],
            "recommended_initial_actions": ["원본 메시지를 보존합니다."],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        }
        return {
            "status": "completed",
            "summary": incident["manager_summary"],
            "incident": incident,
            "risk_segments": incident["risk_chat_segments"],
        }

    def fake_create_notion_report_page(_: dict, __: dict) -> dict:
        return {
            "ok": True,
            "title": "SilentGuard 위험 신호 알림 - incident_demo_room_001",
            "notion_url": "https://notion.so/page_001",
            "notion_page_id": "page_001",
        }

    monkeypatch.setattr(api_module, "request_agent_analysis", fake_agent)
    monkeypatch.setattr(api_module, "create_notion_report_page", fake_create_notion_report_page)

    client = TestClient(api_module.app)
    room = create_test_room(client)
    received_notification_payloads = []

    def fake_send_notification(payload: dict) -> dict:
        received_notification_payloads.append(payload)
        return {
            "channel": "email",
            "status": "sent",
            "sent_at": "2026-08-12T14:30:05+09:00",
            "external_message_id": "smtp-message-001",
            "notion_url": "https://notion.so/page_001",
            "notion_page_id": "page_001",
            "recipient_email": payload["notification_email"],
        }

    monkeypatch.setattr(api_module, "send_notification", fake_send_notification)

    response = client.post(
        "/api/chat/analyze",
        json={"room_id": room["room_id"], "messages": build_immediate_messages()},
    )

    assert response.status_code == 200
    assert response.json()["notification_delivery"]["channel"] == "email"
    assert response.json()["notification_delivery"]["status"] == "sent"
    assert response.json()["notification_delivery"]["external_message_id"] == "smtp-message-001"
    assert response.json()["notification_delivery"]["notion_url"] == "https://notion.so/page_001"
    assert response.json()["notification_delivery"]["notion_page_id"] == "page_001"
    assert response.json()["notification_delivery"]["recipient_email"] == "teacher@example.com"
    assert received_notification_payloads[0]["room_id"] == room["room_id"]
    assert received_notification_payloads[0]["room_name"] == "상담 확인 방"
    assert received_notification_payloads[0]["notification_email"] == "teacher@example.com"
