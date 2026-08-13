"""Phase 1: validate the payload sent from backend to the Agent.

This module does not decide whether a conversation is bullying. It only
checks the agreed input contract and returns a safe, copied payload.
"""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any


REQUIRED_FIELDS = {
    "analysis_id",
    "room_id",
    "bullying_probability",
    "risk_level",
    "messages",
}
MESSAGE_FIELDS = {
    "message_id",
    "sender_id",
    "sender_label",
    "text",
    "created_at",
}
RISK_LEVELS = {"normal", "caution", "warning", "immediate"}


class ContractError(ValueError):
    """Raised when an Agent input payload violates the Phase 1 contract."""


# 필수 문자열 필드가 비어 있지 않은지 확인한다.
def _require_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be a non-empty string")


# ISO-8601 시간 문자열인지 확인한다.
def _validate_timestamp(value: Any, field: str) -> None:
    _require_non_empty_string(value, field)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{field} must be an ISO-8601 timestamp") from exc


# 백엔드에서 Agent로 전달되는 입력 계약을 검증하고 복사한다.
def validate_agent_input(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContractError("payload must be a JSON object")

    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        raise ContractError(f"missing required fields: {', '.join(sorted(missing))}")

    _require_non_empty_string(payload["analysis_id"], "analysis_id")
    _require_non_empty_string(payload["room_id"], "room_id")

    probability = payload["bullying_probability"]
    if isinstance(probability, bool) or not isinstance(probability, (int, float)):
        raise ContractError("bullying_probability must be a number")
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ContractError("bullying_probability must be between 0 and 1")

    if payload["risk_level"] not in RISK_LEVELS:
        raise ContractError("risk_level must be normal, caution, warning, or immediate")

    messages = payload["messages"]
    if not isinstance(messages, list) or not messages:
        raise ContractError("messages must be a non-empty array")

    seen_ids: set[str] = set()
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ContractError(f"messages[{index}] must be an object")
        missing_message_fields = MESSAGE_FIELDS - message.keys()
        if missing_message_fields:
            fields = ", ".join(sorted(missing_message_fields))
            raise ContractError(f"messages[{index}] missing fields: {fields}")
        for field in ("message_id", "sender_id", "sender_label", "text"):
            _require_non_empty_string(message[field], f"messages[{index}].{field}")
        _validate_timestamp(message["created_at"], f"messages[{index}].created_at")
        if message["message_id"] in seen_ids:
            raise ContractError(f"duplicate message_id: {message['message_id']}")
        seen_ids.add(message["message_id"])

    return {
        "analysis_id": payload["analysis_id"],
        "room_id": payload["room_id"],
        "bullying_probability": probability,
        "risk_level": payload["risk_level"],
        "messages": [dict(message) for message in messages],
    }
