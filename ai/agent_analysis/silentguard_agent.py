"""The explicit SilentGuard Agent that turns chat context into JSON analysis."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from ai import config  # noqa: F401  Loads project-root .env.
from ai.agent_analysis.risk_segments import AgentError, INSTRUCTIONS, RISK_SEGMENT_SCHEMA, validate_segments
from ai.notification.incident_notification import (
    INCIDENT_INSTRUCTIONS,
    INCIDENT_SCHEMA,
    build_incident_input,
    validate_incident_notification,
)
from ai.schemas.contract import validate_agent_input


class SilentGuardAgent:
    """Owns the system prompt, user input construction, OpenAI call, and validation."""

    # 환경변수의 모델과 OpenAI client를 Agent에 연결한다.
    def __init__(self, *, client: Any | None = None, model: str | None = None):
        if client is None and not os.getenv("OPENAI_API_KEY"):
            raise AgentError("OPENAI_API_KEY is required to create SilentGuardAgent")
        self.client = client or OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # OpenAI Responses API에 구조화된 JSON 응답을 요청한다.
    def _request_json(self, instructions: str, user_input: str, schema: dict[str, Any], schema_name: str) -> Any:
        return self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=user_input,
            text={"format": {"type": "json_schema", "name": schema_name, "strict": True, "schema": schema}},
        )

    # Responses API 결과에서 JSON 문자열을 꺼내 파싱한다.
    def _parse_json_response(self, response: Any) -> dict[str, Any]:
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise AgentError("OpenAI response did not contain output_text")
        try:
            return json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise AgentError("OpenAI Agent returned non-JSON output") from exc

    # 원본 대화에서 위험 구간만 구조화해 반환한다.
    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated_input = validate_agent_input(payload)
        response = self._request_json(INSTRUCTIONS, json.dumps(validated_input, ensure_ascii=False), RISK_SEGMENT_SCHEMA, "silentguard_risk_segments")
        result = self._parse_json_response(response)
        return validate_segments(result, validated_input["messages"])

    # 원본 대화를 사건과 관리자용 표준 알림으로 분석한다.
    def analyze_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        validated_input = validate_agent_input(payload)
        response = self._request_json(INCIDENT_INSTRUCTIONS, build_incident_input(validated_input), INCIDENT_SCHEMA, "silentguard_incident_notification")
        result = self._parse_json_response(response)
        return validate_incident_notification(result, validated_input["messages"])
