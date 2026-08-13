"""Phase 2: ask an LLM to group risky messages into contextual segments."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from ai import config  # noqa: F401  Loads project-root .env before API calls.
from ai.schemas.contract import ContractError, validate_agent_input


class AgentError(RuntimeError):
    """Raised when the LLM call or its result cannot be safely used."""


RISK_SEGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "risk_chat_segments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "segment_id": {"type": "string"},
                    "start_message_id": {"type": "string"},
                    "end_message_id": {"type": "string"},
                    "evidence_message_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "start_at": {"type": "string"},
                    "end_at": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": [
                    "segment_id",
                    "start_message_id",
                    "end_message_id",
                    "evidence_message_ids",
                    "start_at",
                    "end_at",
                    "reason",
                ],
            },
        },
        "missing_context": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["risk_chat_segments", "missing_context"],
}


INSTRUCTIONS = """너는 SilentGuard의 위험 구간 분석 Agent다.
입력 messages 안의 원본 대화만 근거로 위험 대화의 구간을 구성한다.
위험 표현 한 줄만 떼지 말고 흐름 이해에 필요한 앞뒤 메시지를 구간에 포함한다.
같은 대상·주제·이어지는 시간 흐름이면 묶고, 대상·주제·흐름이 바뀌면 나눈다.
모든 ID와 시간은 입력에 실제로 있는 값을 그대로 사용한다.
확정 판정, 가해자·피해자 지목, 의도 추정은 하지 않는다.
근거가 부족하면 구간을 억지로 만들지 말고 missing_context에 적는다.
위험 신호가 없으면 risk_chat_segments는 빈 배열이어야 한다.
"""


# Agent가 반환한 위험 구간이 입력 메시지에만 연결되는지 검증한다.
def validate_segments(result: Any, messages: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise AgentError("Agent result must be a JSON object")
    segments = result.get("risk_chat_segments")
    missing_context = result.get("missing_context")
    if not isinstance(segments, list) or not isinstance(missing_context, list):
        raise AgentError("Agent result must contain segment and missing_context arrays")

    by_id = {message["message_id"]: message for message in messages}
    seen_segments: set[str] = set()
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise AgentError(f"risk_chat_segments[{index}] must be an object")
        required = {
            "segment_id", "start_message_id", "end_message_id",
            "evidence_message_ids", "start_at", "end_at", "reason",
        }
        if not required <= segment.keys():
            raise AgentError(f"risk_chat_segments[{index}] is missing required fields")
        segment_id = segment["segment_id"]
        if not isinstance(segment_id, str) or not segment_id or segment_id in seen_segments:
            raise AgentError(f"invalid or duplicate segment_id: {segment_id}")
        seen_segments.add(segment_id)
        for field in ("start_message_id", "end_message_id"):
            if segment[field] not in by_id:
                raise AgentError(f"{field} is not present in input messages: {segment[field]}")
        evidence = segment["evidence_message_ids"]
        if not isinstance(evidence, list) or not evidence:
            raise AgentError(f"risk_chat_segments[{index}] needs evidence_message_ids")
        if any(message_id not in by_id for message_id in evidence):
            raise AgentError(f"risk_chat_segments[{index}] contains an unknown evidence ID")
        for field in ("start_at", "end_at"):
            try:
                datetime.fromisoformat(segment[field].replace("Z", "+00:00"))
            except (AttributeError, ValueError) as exc:
                raise AgentError(f"{field} must be an ISO-8601 timestamp") from exc
        if not isinstance(segment["reason"], str) or not segment["reason"].strip():
            raise AgentError(f"risk_chat_segments[{index}] needs a reason")

    if any(not isinstance(item, str) or not item.strip() for item in missing_context):
        raise AgentError("missing_context must contain non-empty strings")
    return result
