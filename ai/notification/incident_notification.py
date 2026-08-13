"""Phase 3: validate the Agent's incident and notification JSON."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ai.agent_analysis.risk_segments import AgentError


DISCLAIMER = "자동 분석된 위험 신호이며 최종 판단이 아닙니다."
RISK_TYPES = {"반복성", "표적성", "집단성", "배제성", "위협성", "공개성"}
FORBIDDEN_PHRASES = ("가해자입니다", "피해자입니다", "학교폭력 사건입니다", "반드시 처벌")

INCIDENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "incident_id": {"type": "string"},
        "risk_chat_segments": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {
            "segment_id": {"type": "string"}, "start_message_id": {"type": "string"}, "end_message_id": {"type": "string"},
            "evidence_message_ids": {"type": "array", "items": {"type": "string"}}, "start_at": {"type": "string"},
            "end_at": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["segment_id", "start_message_id", "end_message_id", "evidence_message_ids", "start_at", "end_at", "reason"]}},
        "suspected_risk_types": {"type": "array", "items": {"type": "object", "additionalProperties": False, "properties": {
            "type": {"type": "string", "enum": list(RISK_TYPES)}, "evidence_message_ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["type", "evidence_message_ids"]}},
        "context_reason": {"type": "string"}, "evidence_message_ids": {"type": "array", "items": {"type": "string"}},
        "manager_summary": {"type": "string"}, "missing_context": {"type": "array", "items": {"type": "string"}},
        "recommended_initial_actions": {"type": "array", "items": {"type": "string"}}, "disclaimer": {"type": "string"}
    },
    "required": ["incident_id", "risk_chat_segments", "suspected_risk_types", "context_reason", "evidence_message_ids", "manager_summary", "missing_context", "recommended_initial_actions", "disclaimer"]
}


INCIDENT_INSTRUCTIONS = """너는 SilentGuard의 사건·알림 Agent다.
원본 messages 안에서 서로 연결되는 위험 구간을 하나의 사건으로 정리한다.
원문에 실제로 있는 내용만 사용하고, 위험 유형마다 근거 메시지 ID를 연결한다.
학교폭력, 가해자, 피해자, 의도, 처벌을 확정하지 않는다.
관리자 요약은 위험 신호와 추가 확인 필요성을 2~4문장으로 쓴다.
초기 조치는 원본 보존, 앞뒤 대화 확인, 당사자 상황 확인처럼 검토 중심으로 쓴다.
disclaimer는 반드시 "자동 분석된 위험 신호이며 최종 판단이 아닙니다."로 반환한다.
반드시 JSON Schema에 맞는 결과만 반환한다.
"""


# Agent가 사건 분석에 사용할 원본 입력을 JSON 문자열로 만든다.
def build_incident_input(payload: dict[str, Any]) -> str:
    import json
    return json.dumps(payload, ensure_ascii=False)


# 입력 메시지 ID 집합을 만들어 근거 검증에 사용한다.
def collect_message_ids(messages: list[dict[str, Any]]) -> set[str]:
    return {message["message_id"] for message in messages}


# 문자열 안에 확정 판정 금지 표현이 있는지 확인한다.
def contains_forbidden_claim(value: str) -> bool:
    return any(phrase in value for phrase in FORBIDDEN_PHRASES)


# Agent 사건 결과의 필수 필드와 원본 근거 연결을 검증한다.
def validate_incident_notification(result: Any, messages: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise AgentError("사건 결과는 JSON 객체여야 합니다")
    required = {"incident_id", "risk_chat_segments", "suspected_risk_types", "context_reason", "evidence_message_ids", "manager_summary", "missing_context", "recommended_initial_actions", "disclaimer"}
    if not required <= result.keys():
        raise AgentError("사건 결과에 필수 필드가 없습니다")
    message_ids = collect_message_ids(messages)
    if not isinstance(result["incident_id"], str) or not result["incident_id"].strip():
        raise AgentError("incident_id가 올바르지 않습니다")
    if not isinstance(result["disclaimer"], str) or "자동 분석" not in result["disclaimer"] or "최종 판단" not in result["disclaimer"]:
        raise AgentError("disclaimer가 안전 문구가 아닙니다")
    result["disclaimer"] = DISCLAIMER
    all_evidence = set(result["evidence_message_ids"])
    for segment in result["risk_chat_segments"]:
        if segment["start_message_id"] not in message_ids or segment["end_message_id"] not in message_ids:
            raise AgentError("위험 구간의 시작·종료 ID가 원본에 없습니다")
        if not segment["evidence_message_ids"] or not set(segment["evidence_message_ids"]) <= message_ids:
            raise AgentError("위험 구간 근거 ID가 원본에 없습니다")
        all_evidence.update(segment["evidence_message_ids"])
        for field in ("start_at", "end_at"):
            try:
                datetime.fromisoformat(segment[field].replace("Z", "+00:00"))
            except (AttributeError, ValueError) as exc:
                raise AgentError("위험 구간 시간이 올바르지 않습니다") from exc
        if contains_forbidden_claim(segment["reason"]):
            raise AgentError("위험 구간 이유에 확정 판정 표현이 있습니다")
    if not set(result["evidence_message_ids"]) <= message_ids:
        raise AgentError("사건 근거 ID가 원본에 없습니다")
    for risk_type in result["suspected_risk_types"]:
        if risk_type["type"] not in RISK_TYPES or not set(risk_type["evidence_message_ids"]) <= message_ids:
            raise AgentError("위험 유형의 근거 ID가 올바르지 않습니다")
        all_evidence.update(risk_type["evidence_message_ids"])
    text_fields = [result["context_reason"], result["manager_summary"], *result["missing_context"], *result["recommended_initial_actions"]]
    if any(contains_forbidden_claim(text) for text in text_fields):
        raise AgentError("알림 내용에 확정 판정 표현이 있습니다")
    return result
