"""Send SilentGuard Notion report links through SMTP email."""

from __future__ import annotations

from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
import os
import smtplib
import ssl
from typing import Any

from ai import config  # noqa: F401  Loads project-root .env.
from ai.agent_analysis.risk_segments import AgentError


REQUIRED_EMAIL_CONFIG_KEYS = (
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "EMAIL_FROM",
    "EMAIL_USE_TLS",
)


# 이메일 환경변수 문자열을 안전하게 정리한다.
def read_email_env(name: str) -> str:
    return os.getenv(name, "").strip()


# SMTP 이메일 발송에 필요한 환경설정을 읽고 검증한다.
def load_email_config() -> dict[str, Any]:
    values = {name: read_email_env(name) for name in REQUIRED_EMAIL_CONFIG_KEYS}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise AgentError(f"missing email config: {', '.join(missing)}")
    try:
        port = int(values["SMTP_PORT"])
    except ValueError as exc:
        raise AgentError("SMTP_PORT must be an integer") from exc
    return {
        "host": values["SMTP_HOST"],
        "port": port,
        "username": values["SMTP_USERNAME"],
        "password": values["SMTP_PASSWORD"],
        "from_email": values["EMAIL_FROM"],
        "use_tls": values["EMAIL_USE_TLS"].lower() in {"1", "true", "yes", "on"},
        "from_name": read_email_env("EMAIL_FROM_NAME") or "SilentGuard",
    }


# Notion 링크 이메일 제목을 만든다.
def build_email_subject(payload: dict[str, Any]) -> str:
    return "REDPLAG [위험 신호 알림]"


# Agent 결과에서 위험 유형 표시 문구를 만든다.
def build_risk_type_text(incident: dict[str, Any]) -> str:
    risk_types = [
        risk_type.get("type", "")
        for risk_type in incident.get("suspected_risk_types", [])
        if risk_type.get("type")
    ]
    return ", ".join(risk_types) if risk_types else "-"


# 위험 구간 또는 원본 메시지 기준으로 채팅 시간 표시 문구를 만든다.
def build_chat_time_text(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    risk_segments = incident.get("risk_chat_segments", [])
    if risk_segments:
        start_at = risk_segments[0].get("start_at", "")
        end_at = risk_segments[-1].get("end_at", "")
        if start_at and end_at:
            return format_chat_time_range(start_at, end_at)

    messages = payload.get("messages", [])
    if messages:
        start_at = messages[0].get("created_at", "")
        end_at = messages[-1].get("created_at", "")
        if start_at and end_at:
            return format_chat_time_range(start_at, end_at)
    return "-"


# ISO 시간 문자열을 이메일 표시용 datetime으로 바꾼다.
def parse_email_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# 이메일에 표시할 날짜와 시간을 한국어 형식으로 만든다.
def format_email_datetime(value: datetime) -> str:
    return f"{value.year}년 {value.month}월 {value.day}일 {value.hour:02d}:{value.minute:02d}"


# 이메일에 표시할 채팅 시간 범위를 읽기 쉽게 만든다.
def format_chat_time_range(start_at: str, end_at: str) -> str:
    start_datetime = parse_email_datetime(start_at)
    end_datetime = parse_email_datetime(end_at)
    if start_datetime is None or end_datetime is None:
        return f"{start_at} ~ {end_at}"
    if start_datetime.date() == end_datetime.date():
        return (
            f"{format_email_datetime(start_datetime)} ~ "
            f"{end_datetime.hour:02d}:{end_datetime.minute:02d}"
        )
    return f"{format_email_datetime(start_datetime)} ~ {format_email_datetime(end_datetime)}"


# Notion 링크 이메일 본문을 만든다.
def build_email_body(payload: dict[str, Any], notion_result: dict[str, Any]) -> str:
    incident = payload.get("incident", {})
    probability = payload.get("bullying_probability")
    if isinstance(probability, (int, float)):
        probability_text = f"{round(float(probability) * 100)}%"
    else:
        probability_text = "-"
    return "\n".join(
        [
            "REDPLAG [위험 신호 알림]",
            "",
            f"채팅방: {payload.get('room_name', '')}",
            f"위험 유형: {build_risk_type_text(incident)}",
            f"채팅 시간: {build_chat_time_text(payload, incident)}",
            f"위험 단계: {payload.get('risk_level', '')}",
            f"괴롭힘 가능성: {probability_text}",
            "",
            "관리자용 요약:",
            incident.get("manager_summary", ""),
            "",
            "Notion 보고서:",
            notion_result.get("notion_url", ""),
            "",
            "자동 분석된 위험 신호이며 최종 판단이 아닙니다. 원본 대화와 앞뒤 맥락을 확인해주세요.",
        ]
    )


# SMTP로 보낼 이메일 메시지를 구성한다.
def build_email_message(
    payload: dict[str, Any], notion_result: dict[str, Any], config_values: dict[str, Any]
) -> EmailMessage:
    recipient_email = payload.get("notification_email")
    if not isinstance(recipient_email, str) or not recipient_email.strip():
        raise AgentError("notification_email is required for email delivery")
    message = EmailMessage()
    message["Subject"] = build_email_subject(payload)
    message["From"] = formataddr((config_values["from_name"], config_values["from_email"]))
    message["To"] = recipient_email.strip()
    message["Message-ID"] = make_msgid(domain="silentguard.local")
    message.set_content(build_email_body(payload, notion_result))
    return message


# SMTP 연결을 열고 이메일 메시지를 전송한다.
def send_email_message(message: EmailMessage, config_values: dict[str, Any]) -> str:
    try:
        if config_values["port"] == 465 and config_values["use_tls"]:
            with smtplib.SMTP_SSL(
                config_values["host"],
                config_values["port"],
                timeout=20,
                context=ssl.create_default_context(),
            ) as server:
                server.login(config_values["username"], config_values["password"])
                server.send_message(message)
        else:
            with smtplib.SMTP(
                config_values["host"], config_values["port"], timeout=20
            ) as server:
                server.ehlo()
                if config_values["use_tls"]:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(config_values["username"], config_values["password"])
                server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise AgentError(f"email delivery failed: {exc}") from exc
    return str(message["Message-ID"])


# Notion 보고서 링크를 수신 이메일로 전송하고 전달 상태를 반환한다.
def send_notion_link_email(payload: dict[str, Any], notion_result: dict[str, Any]) -> dict[str, Any]:
    config_values = load_email_config()
    message = build_email_message(payload, notion_result, config_values)
    external_message_id = send_email_message(message, config_values)
    return {
        "channel": "email",
        "status": "sent",
        "recipient_email": message["To"],
        "sent_at": datetime.now().astimezone().isoformat(),
        "external_message_id": external_message_id,
    }
