from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import back.api as api
from back.api import app


@pytest.fixture(autouse=True)
def use_mock_model_for_phase_contract_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(api.MODEL_PROVIDER_ENV, "mock")


# Phase 테스트용 채팅방을 만들고 백엔드 생성 room_id를 반환한다.
def create_test_room(client: TestClient, room_name: str = "테스트 채팅방") -> dict:
    response = client.post(
        "/api/chat/rooms",
        json={"room_name": room_name, "notification_email": "teacher@example.com"},
    )

    assert response.status_code == 200
    return response.json()


# Phase 테스트용 원본 메시지 형식을 만든다.
def make_message(message_id: str, sender_id: str, text: str, created_at: str) -> dict:
    return {
        "message_id": message_id,
        "sender_id": sender_id,
        "sender_label": sender_id,
        "text": text,
        "created_at": created_at,
    }


# 문서에 있는 네 가지 데모 대화를 만든다.
def build_demo_messages(scenario: str) -> list[dict]:
    samples = {
        "normal": [
            ("A", "오늘 체육복 챙겼어?"),
            ("B", "응 챙겼어."),
            ("A", "끝나고 같이 매점 갈래?"),
        ],
        "caution": [
            ("A", "너 오늘 왜 답이 이렇게 늦어?"),
            ("B", "학원 다녀오느라 조금 늦었어."),
            ("A", "다음에는 바로 답해. 다들 기다리잖아."),
        ],
        "warning": [
            ("A", "또 실수했네. 너 때문에 분위기 다 망쳤어."),
            ("B", "미안, 다음에는 조심할게."),
            ("C", "항상 저래. 그냥 빼고 하자."),
        ],
        "immediate": [
            ("A", "너 왜 또 여기 들어왔냐"),
            ("B", "그냥 얘기하려고"),
            ("A", "아무도 너랑 말하기 싫대"),
            ("C", "맞아 그냥 나가"),
        ],
    }
    return [
        make_message(
            f"msg_{index:03d}",
            sender_id,
            text,
            f"2026-08-08T14:{28 + index:02d}:00+09:00",
        )
        for index, (sender_id, text) in enumerate(samples[scenario], start=1)
    ]


# Phase 01에서 프론트엔드가 채팅방 이름과 필수 이메일로 방을 생성하는지 확인한다.
def test_phase_01_creates_chat_room_with_required_notification_email() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/chat/rooms",
        json={"room_name": "1학년 3반 단체방", "notification_email": "teacher@example.com"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["room_id"].startswith("room_")
    assert result["room_name"] == "1학년 3반 단체방"
    assert result["notification_email"] == "teacher@example.com"
    assert isinstance(result["created_at"], str)


# Phase 01에서 생성된 채팅방 목록을 프론트엔드가 조회할 수 있는지 확인한다.
def test_phase_01_lists_created_chat_rooms() -> None:
    client = TestClient(app)
    room = create_test_room(client, "목록 확인 방")

    response = client.get("/api/chat/rooms")

    assert response.status_code == 200
    assert room in response.json()


# Phase 01에서 이메일 없이 채팅방 생성을 요청하면 입력 오류를 반환하는지 확인한다.
def test_phase_01_rejects_chat_room_without_notification_email() -> None:
    client = TestClient(app)

    response = client.post("/api/chat/rooms", json={"room_name": "이메일 없는 방"})

    assert response.status_code == 400
    assert response.json()["error_code"] == "room_email_required"


# Phase 01에서 생성되지 않은 채팅방 분석 요청을 거부하는지 확인한다.
def test_phase_01_rejects_analysis_for_unknown_chat_room() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/chat/analyze",
        json={"room_id": "room_missing", "messages": build_demo_messages("normal")},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "room_not_found"


# Phase 01에서 room_id 없이 분석을 요청하면 입력 오류를 반환하는지 확인한다.
def test_phase_01_rejects_analysis_without_room_id() -> None:
    client = TestClient(app)

    response = client.post("/api/chat/analyze", json={"messages": build_demo_messages("normal")})

    assert response.status_code == 400
    assert response.json()["error_code"] == "room_id_required"


# Phase 01 요청이 analysis_id 없이 서버에 전달되는지 확인한다.
def test_phase_01_accepts_documented_frontend_payload() -> None:
    client = TestClient(app)
    room = create_test_room(client)

    response = client.post(
        "/api/chat/analyze",
        json={"room_id": room["room_id"], "messages": build_demo_messages("normal")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["room_id"] == room["room_id"]
    assert result["analysis_id"].startswith(f"analysis_{room['room_id']}_")


# Phase 02 모델 입력은 시간순 원본 메시지 묶음인지 확인한다.
def test_phase_02_sorts_messages_before_mock_model_scoring() -> None:
    client = TestClient(app)
    room = create_test_room(client)
    messages = build_demo_messages("normal")

    response = client.post(
        "/api/chat/analyze",
        json={"room_id": room["room_id"], "messages": list(reversed(messages))},
    )

    assert response.status_code == 200
    assert [message["message_id"] for message in response.json()["messages"]] == [
        "msg_001",
        "msg_002",
        "msg_003",
    ]


# Phase 03 mock 모델 결과와 백엔드 위험 단계가 문서 기준과 일치하는지 확인한다.
def test_phase_03_returns_documented_mock_probability_and_risk_level() -> None:
    client = TestClient(app)
    room = create_test_room(client)

    expected_results = {
        "normal": (0.24, "normal"),
        "caution": (0.58, "caution"),
        "warning": (0.75, "warning"),
        "immediate": (0.91, "immediate"),
    }

    for scenario, (probability, risk_level) in expected_results.items():
        response = client.post(
            "/api/chat/analyze",
            json={"room_id": room["room_id"], "messages": build_demo_messages(scenario)},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["bullying_probability"] == probability
        assert result["risk_level"] == risk_level


# 백엔드 모델 설정 기본값이 실제 로컬 모델인지 확인한다.
def test_phase_03_model_provider_defaults_to_real(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(api.MODEL_PROVIDER_ENV, raising=False)
    monkeypatch.setattr(api, "get_bullying_probability", lambda messages: 0.31)

    probability = api.get_configured_bullying_probability([SimpleNamespace(text="확인 메시지")])

    assert probability == 0.31
