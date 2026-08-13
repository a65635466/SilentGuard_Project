from email.message import EmailMessage

import pytest

from ai.agent_analysis.risk_segments import AgentError
from ai.notification import email_delivery


class FakeSMTP:
    sent_messages: list[EmailMessage] = []
    login_arguments: tuple[str, str] | None = None
    started_tls = False

    # SMTP 테스트 더블의 세션 상태를 초기화한다.
    @classmethod
    def reset(cls) -> None:
        cls.sent_messages = []
        cls.login_arguments = None
        cls.started_tls = False

    # SMTP 연결 인자를 보존한다.
    def __init__(self, host: str, port: int, timeout: int):
        self.host = host
        self.port = port
        self.timeout = timeout

    # 컨텍스트 매니저 진입 시 자기 자신을 반환한다.
    def __enter__(self):
        return self

    # 컨텍스트 매니저 종료 처리를 수행한다.
    def __exit__(self, *_):
        return False

    # SMTP 인사 명령을 테스트에서 무해하게 처리한다.
    def ehlo(self) -> None:
        return None

    # TLS 시작 여부를 기록한다.
    def starttls(self, context) -> None:
        self.__class__.started_tls = context is not None

    # SMTP 로그인 인자를 기록한다.
    def login(self, username: str, password: str) -> None:
        self.__class__.login_arguments = (username, password)

    # 발송된 이메일 메시지를 기록한다.
    def send_message(self, message: EmailMessage) -> None:
        self.__class__.sent_messages.append(message)


# Phase 08에서 Notion 링크 이메일을 SMTP로 발송하는지 확인한다.
def test_phase_08_sends_notion_link_email_with_smtp(monkeypatch) -> None:
    FakeSMTP.reset()
    monkeypatch.setattr(email_delivery.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setenv("SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")
    monkeypatch.setenv("EMAIL_USE_TLS", "true")
    monkeypatch.setenv("EMAIL_FROM_NAME", "SilentGuard")

    result = email_delivery.send_notion_link_email(
        {
            "analysis_id": "analysis_001",
            "room_name": "상담 확인 방",
            "notification_email": "teacher@example.com",
            "risk_level": "immediate",
            "bullying_probability": 0.91,
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
                    "created_at": "2026-08-08T14:31:00+09:00",
                },
            ],
            "incident": {
                "incident_id": "incident_001",
                "manager_summary": "원본 대화에서 배제 위험 신호가 보입니다.",
                "suspected_risk_types": [
                    {"type": "배제성", "evidence_message_ids": ["msg_001", "msg_002"]}
                ],
                "risk_chat_segments": [
                    {
                        "start_at": "2026-08-08T14:28:00+09:00",
                        "end_at": "2026-08-08T14:31:00+09:00",
                    }
                ],
            },
        },
        {
            "title": "SilentGuard 위험 신호 알림 - incident_001",
            "notion_url": "https://notion.so/page_001",
            "notion_page_id": "page_001",
        },
    )

    assert result["channel"] == "email"
    assert result["status"] == "sent"
    assert result["recipient_email"] == "teacher@example.com"
    assert result["external_message_id"]
    assert FakeSMTP.started_tls is True
    assert FakeSMTP.login_arguments == ("sender@example.com", "app-password")
    assert len(FakeSMTP.sent_messages) == 1
    message = FakeSMTP.sent_messages[0]
    assert message["To"] == "teacher@example.com"
    assert message["From"] == "SilentGuard <sender@example.com>"
    assert message["Subject"] == "REDPLAG [위험 신호 알림]"
    content = message.get_content()
    assert "분석 ID:" not in content
    assert "사건 ID:" not in content
    assert "위험 유형: 배제성" in content
    assert "채팅 시간: 2026년 8월 8일 14:28 ~ 14:31" in content
    assert "https://notion.so/page_001" in content
    assert "원본 대화에서 배제 위험 신호가 보입니다." in content


# Phase 08에서 SMTP 설정 누락 시 이메일 발송을 시도하지 않고 중단하는지 확인한다.
def test_phase_08_rejects_missing_smtp_config(monkeypatch) -> None:
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "app-password")
    monkeypatch.setenv("EMAIL_FROM", "sender@example.com")
    monkeypatch.setenv("EMAIL_USE_TLS", "true")

    with pytest.raises(AgentError, match="SMTP_HOST"):
        email_delivery.load_email_config()
