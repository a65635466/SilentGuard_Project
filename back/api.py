"""CORS로 분리된 SilentGuard 백엔드 채팅 분석 API."""

from __future__ import annotations

from datetime import datetime
import os
import re
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from ai.agent_analysis.silentguard_agent import SilentGuardAgent
from ai.agent_analysis.risk_segments import AgentError
from ai.model.mock_model import get_mock_bullying_probability
from ai.model.predict import get_bullying_probability
from ai.notification.email_delivery import send_notion_link_email
from ai.notification.notion_delivery import create_notion_report_page


ALLOWED_FRONTEND_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]
MODEL_PROVIDER_ENV = "SILENTGUARD_MODEL_PROVIDER"


class ChatMessage(BaseModel):
    """프론트엔드와 Agent가 공유하는 원본 메시지 형식이다."""

    message_id: str
    sender_id: str
    sender_label: str
    text: str
    created_at: datetime

    model_config = ConfigDict(extra="forbid")


class AnalyzeChatRequest(BaseModel):
    """프론트엔드 분석 요청 형식이다."""

    room_id: str | None = None
    messages: list[ChatMessage]

    model_config = ConfigDict(extra="forbid")


class CreateChatRoomRequest(BaseModel):
    """프론트엔드 채팅방 생성 요청 형식이다."""

    room_name: str | None = None
    notification_email: str | None = None

    model_config = ConfigDict(extra="forbid")


CHAT_ROOMS: dict[str, dict[str, str]] = {}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 잘못된 요청 본문을 프론트엔드용 입력 오류로 바꾼다.
@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_, __) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": "invalid message payload"})


# 메시지를 원본 시간순으로 정렬해 분석 묶음을 만든다.
def build_recent_message_bundle(messages: list[ChatMessage]) -> list[ChatMessage]:
    return sorted(messages, key=lambda message: message.created_at)


# 채팅방을 식별하는 백엔드 전용 ID를 만든다.
def build_room_id() -> str:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d%H%M%S")
    return f"room_{timestamp}_{uuid4().hex[:6]}"


# 분석 요청을 식별하는 백엔드 전용 ID를 만든다.
def build_analysis_id(room_id: str) -> str:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d%H%M%S")
    return f"analysis_{room_id}_{timestamp}_{uuid4().hex[:6]}"


# 사용자 입력 문자열의 앞뒤 공백을 제거한다.
def normalize_required_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


# 이메일 기본 형식이 MVP 입력 조건을 만족하는지 확인한다.
def is_valid_notification_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(email))


# 채팅방 생성 요청을 검증하고 정리된 값을 반환한다.
def validate_chat_room_request(request: CreateChatRoomRequest) -> tuple[str, str]:
    room_name = normalize_required_text(request.room_name)
    notification_email = normalize_required_text(request.notification_email)

    if not room_name:
        raise HTTPException(
            status_code=400,
            detail={
                "detail": "room_name is required",
                "error_code": "room_name_required",
                "user_message": "채팅방 이름을 입력해주세요.",
            },
        )
    if not notification_email:
        raise HTTPException(
            status_code=400,
            detail={
                "detail": "notification_email is required",
                "error_code": "room_email_required",
                "user_message": "Notion 링크를 받을 이메일을 입력해주세요.",
            },
        )
    if not is_valid_notification_email(notification_email):
        raise HTTPException(
            status_code=400,
            detail={
                "detail": "notification_email is invalid",
                "error_code": "room_email_invalid",
                "user_message": "이메일 형식을 확인해주세요.",
            },
        )
    return room_name, notification_email


# 채팅방 저장소에 넣을 표준 채팅방 객체를 만든다.
def build_chat_room(room_name: str, notification_email: str) -> dict[str, str]:
    return {
        "room_id": build_room_id(),
        "room_name": room_name,
        "notification_email": notification_email,
        "created_at": datetime.now().astimezone().isoformat(),
    }


# 채팅방 객체를 프론트엔드 응답용 JSON으로 복사한다.
def serialize_chat_room(room: dict[str, str]) -> dict[str, str]:
    return {
        "room_id": room["room_id"],
        "room_name": room["room_name"],
        "notification_email": room["notification_email"],
        "created_at": room["created_at"],
    }


# 분석 요청의 room_id에 해당하는 채팅방을 찾는다.
def find_chat_room_or_raise(room_id: str) -> dict[str, str]:
    room = CHAT_ROOMS.get(room_id)
    if room is None:
        raise HTTPException(
            status_code=404,
            detail={
                "detail": "chat room not found",
                "error_code": "room_not_found",
                "user_message": "채팅방을 먼저 생성해주세요.",
            },
        )
    return room


# 모델 확률을 문서의 네 단계 위험도로 변환한다.
def calculate_risk_level(probability: float) -> str:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("bullying_probability must be between 0.0 and 1.0")
    if probability < 0.50:
        return "normal"
    if probability < 0.70:
        return "caution"
    if probability < 0.85:
        return "warning"
    return "immediate"


# 환경 설정에 따라 mock 모델 또는 실제 로컬 모델 확률을 반환한다.
def get_configured_bullying_probability(messages: list[ChatMessage]) -> float:
    provider = os.getenv(MODEL_PROVIDER_ENV, "real").strip().lower()
    if provider == "mock":
        return get_mock_bullying_probability(messages)
    return get_bullying_probability(messages)


# 위험 단계가 Agent 분석을 요청해야 하는지 확인한다.
def should_request_agent_analysis(risk_level: str) -> bool:
    return risk_level in {"warning", "immediate"}


# Pydantic 메시지를 공통 JSON 메시지 형식으로 바꾼다.
def serialize_messages(messages: list[ChatMessage]) -> list[dict[str, str]]:
    return [
        {
            "message_id": message.message_id,
            "sender_id": message.sender_id,
            "sender_label": message.sender_label,
            "text": message.text,
            "created_at": message.created_at.isoformat(),
        }
        for message in messages
    ]


# Phase 04 계약에 맞는 백엔드에서 Agent로의 입력을 만든다.
def build_agent_analysis_request(
    analysis_id: str,
    room_id: str,
    messages: list[ChatMessage],
    bullying_probability: float,
    risk_level: str,
) -> dict[str, Any]:
    return {
        "analysis_id": analysis_id,
        "room_id": room_id,
        "bullying_probability": bullying_probability,
        "risk_level": risk_level,
        "messages": serialize_messages(messages),
    }


# Agent 표준 출력을 Phase 07 프론트엔드 응답 필드로 감싼다.
def request_agent_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    incident = SilentGuardAgent().analyze_incident(payload)
    return {
        "status": "completed",
        "summary": incident["manager_summary"],
        "incident": incident,
        "risk_segments": incident["risk_chat_segments"],
    }


# 알림 전송이 필요하지 않은 상태를 만든다.
def build_notification_delivery(
    status: str = "not_required", recipient_email: str | None = None
) -> dict[str, Any]:
    return {
        "channel": "none",
        "status": status,
        "sent_at": None,
        "external_message_id": None,
        "recipient_email": recipient_email,
    }


# Agent 결과 안의 근거 메시지 ID를 모두 수집한다.
def extract_agent_message_ids(agent_response: dict[str, Any]) -> set[str]:
    message_ids: set[str] = set()
    incident = agent_response.get("incident", {})
    sources = [agent_response, incident] if isinstance(incident, dict) else [agent_response]
    for source in sources:
        for key in ("message_ids", "evidence_message_ids"):
            values = source.get(key, [])
            if isinstance(values, list):
                message_ids.update(value for value in values if isinstance(value, str))
        for segment in source.get("risk_chat_segments", source.get("risk_segments", [])):
            if isinstance(segment, dict):
                values = segment.get("evidence_message_ids", segment.get("message_ids", []))
                if isinstance(values, list):
                    message_ids.update(value for value in values if isinstance(value, str))
    return message_ids


# Agent 근거가 입력 원본 메시지 ID만 참조하는지 확인한다.
def has_only_known_message_ids(
    agent_response: dict[str, Any], messages: list[ChatMessage]
) -> bool:
    known_message_ids = {message.message_id for message in messages}
    return extract_agent_message_ids(agent_response).issubset(known_message_ids)


# Notion 설정 누락 오류인지 확인한다.
def is_notion_not_configured_error(error: AgentError) -> bool:
    message = str(error)
    return "NOTION_TOKEN is required" in message or "NOTION_PARENT_PAGE_ID is required" in message


# SMTP 이메일 설정 누락 오류인지 확인한다.
def is_email_not_configured_error(error: AgentError) -> bool:
    return str(error).startswith("missing email config:")


# 이메일 설정 누락을 프론트엔드 알림 전달 상태로 바꾼다.
def build_email_not_configured_delivery(
    notion_result: dict[str, Any], recipient_email: str | None = None
) -> dict[str, Any]:
    return {
        "channel": "email",
        "status": "email_not_configured",
        "sent_at": None,
        "external_message_id": None,
        "notion_url": notion_result.get("notion_url"),
        "notion_page_id": notion_result.get("notion_page_id"),
        "recipient_email": recipient_email,
    }


# 이메일 전송 실패를 분석 응답에 남길 전달 상태로 바꾼다.
def build_failed_email_delivery(
    error: AgentError, notion_result: dict[str, Any], recipient_email: str | None = None
) -> dict[str, Any]:
    return {
        "channel": "email",
        "status": "email_failed",
        "sent_at": None,
        "external_message_id": None,
        "notion_url": notion_result.get("notion_url"),
        "notion_page_id": notion_result.get("notion_page_id"),
        "error": str(error),
        "recipient_email": recipient_email,
    }


# Notion 생성 실패를 분석 응답에 남길 전달 상태로 바꾼다.
def build_failed_notion_delivery(
    error: AgentError, recipient_email: str | None = None
) -> dict[str, Any]:
    return {
        "channel": "notion",
        "status": "notion_failed",
        "sent_at": None,
        "external_message_id": None,
        "error": str(error),
        "recipient_email": recipient_email,
    }


# 검증된 Agent 사건을 Notion 보고서와 이메일 알림으로 전송 처리한다.
def send_notification(payload: dict[str, Any]) -> dict[str, Any]:
    recipient_email = payload.get("notification_email")
    try:
        notion_result = create_notion_report_page(payload, payload["incident"])
    except AgentError as exc:
        if is_notion_not_configured_error(exc):
            return build_failed_notion_delivery(exc, recipient_email=recipient_email)
        return build_failed_notion_delivery(exc, recipient_email=recipient_email)
    try:
        email_result = send_notion_link_email(payload, notion_result)
    except AgentError as exc:
        if is_email_not_configured_error(exc):
            return build_email_not_configured_delivery(notion_result, recipient_email)
        return build_failed_email_delivery(exc, notion_result, recipient_email)
    return {
        **email_result,
        "notion_url": notion_result.get("notion_url"),
        "notion_page_id": notion_result.get("notion_page_id"),
    }


# 프론트엔드가 입력한 이름과 이메일로 새 채팅방을 만든다.
@app.post("/api/chat/rooms")
async def create_chat_room(request: CreateChatRoomRequest) -> Any:
    try:
        room_name, notification_email = validate_chat_room_request(request)
    except HTTPException as exc:
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        raise
    room = build_chat_room(room_name, notification_email)
    CHAT_ROOMS[room["room_id"]] = room
    return serialize_chat_room(room)


# 프론트엔드가 생성된 채팅방 목록을 확인할 수 있게 반환한다.
@app.get("/api/chat/rooms")
async def list_chat_rooms() -> list[dict[str, str]]:
    return [serialize_chat_room(room) for room in CHAT_ROOMS.values()]


# 프론트엔드가 보낸 채팅을 분석하고 Phase 07 응답으로 반환한다.
@app.post("/api/chat/analyze")
async def analyze_chat(request: AnalyzeChatRequest) -> dict[str, Any]:
    if not request.room_id or not request.room_id.strip():
        return JSONResponse(
            status_code=400,
            content={
                "detail": "room_id is required",
                "error_code": "room_id_required",
                "user_message": "채팅방을 먼저 선택해주세요.",
            },
        )
    room_id = request.room_id.strip()
    try:
        chat_room = find_chat_room_or_raise(room_id)
    except HTTPException as exc:
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        raise
    if not request.messages:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "messages must not be empty",
                "error_code": "input_required",
                "user_message": "분석할 채팅을 입력해주세요.",
            },
        )

    messages = build_recent_message_bundle(request.messages)
    analysis_id = build_analysis_id(room_id)
    bullying_probability = get_configured_bullying_probability(messages)
    risk_level = calculate_risk_level(bullying_probability)
    incident: dict[str, Any] = {}
    risk_segments: list[dict[str, Any]] = []
    agent_response: dict[str, Any] = {}
    notification_delivery = build_notification_delivery(
        recipient_email=chat_room["notification_email"]
    )

    if should_request_agent_analysis(risk_level):
        agent_payload = build_agent_analysis_request(
            analysis_id,
            room_id,
            messages,
            bullying_probability,
            risk_level,
        )
        try:
            agent_response = request_agent_analysis(agent_payload)
            incident = agent_response["incident"]
            risk_segments = agent_response["risk_segments"]
            if not has_only_known_message_ids(agent_response, messages):
                notification_delivery = build_notification_delivery(
                    "skipped_invalid_message_id", chat_room["notification_email"]
                )
            else:
                notification_delivery = send_notification(
                    {
                        "analysis_id": analysis_id,
                        "room_id": room_id,
                        "room_name": chat_room["room_name"],
                        "notification_email": chat_room["notification_email"],
                        "messages": agent_payload["messages"],
                        "bullying_probability": bullying_probability,
                        "risk_level": risk_level,
                        "incident": incident,
                    }
                )
        except Exception:
            agent_response = {"status": "agent_failed", "retryable": True}

    return {
        "analysis_id": analysis_id,
        "room_id": room_id,
        "room_name": chat_room["room_name"],
        "notification_email": chat_room["notification_email"],
        "messages": serialize_messages(messages),
        "bullying_probability": bullying_probability,
        "risk_level": risk_level,
        "incident": incident,
        "risk_segments": risk_segments,
        "agent_response": agent_response,
        "notification_delivery": notification_delivery,
    }
