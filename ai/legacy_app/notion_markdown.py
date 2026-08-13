"""Build a Notion-ready Markdown report from a SilentGuard incident result."""

from __future__ import annotations

from pathlib import Path
from typing import Any


# Markdown 표 셀에서 깨질 수 있는 문자를 안전하게 바꾼다.
def escape_table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


# 메시지 ID로 원본 메시지를 빠르게 찾을 수 있는 사전을 만든다.
def index_messages_by_id(messages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {message["message_id"]: message for message in messages}


# 리스트 값을 Markdown bullet 목록으로 만든다.
def build_bullet_list(items: list[Any]) -> str:
    if not items:
        return "- 없음"
    return "\n".join(f"- {item}" for item in items)


# 보고서 상단의 기본 요약 섹션을 만든다.
def build_summary_section(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    probability = payload.get("bullying_probability", "")
    if isinstance(probability, float):
        probability = f"{probability:.2f}"
    lines = [
        "## 1. 요약",
        "",
        f"- 분석 ID: {payload.get('analysis_id', '')}",
        f"- 사건 ID: {incident.get('incident_id', '')}",
        f"- 채팅방 ID: {payload.get('room_id', '')}",
        f"- 위험 단계: {payload.get('risk_level', '')}",
        f"- 괴롭힘 위험 확률: {probability}",
    ]
    return "\n".join(lines)


# 관리자가 먼저 읽을 요약과 맥락 설명 섹션을 만든다.
def build_manager_section(incident: dict[str, Any]) -> str:
    return "\n".join([
        "## 2. 관리자 확인 내용",
        "",
        incident.get("manager_summary", ""),
        "",
        "## 3. 맥락상 위험 이유",
        "",
        incident.get("context_reason", ""),
    ])


# 의심 위험 유형을 Markdown 표로 만든다.
def build_risk_types_table(incident: dict[str, Any]) -> str:
    lines = ["## 4. 감지된 위험 유형", "", "| 유형 | 근거 메시지 |", "|---|---|"]
    for risk_type in incident.get("suspected_risk_types", []):
        evidence_ids = ", ".join(risk_type.get("evidence_message_ids", []))
        lines.append(f"| {escape_table_cell(risk_type.get('type', ''))} | {escape_table_cell(evidence_ids)} |")
    if len(lines) == 4:
        lines.append("| 없음 | 없음 |")
    return "\n".join(lines)


# Agent가 잡은 위험 구간을 Markdown 표로 만든다.
def build_risk_segments_table(incident: dict[str, Any]) -> str:
    lines = ["## 5. 위험 구간", "", "| 구간 | 시간 | 이유 | 근거 메시지 |", "|---|---|---|---|"]
    for segment in incident.get("risk_chat_segments", []):
        time_range = f"{segment.get('start_at', '')} ~ {segment.get('end_at', '')}"
        evidence_ids = ", ".join(segment.get("evidence_message_ids", []))
        lines.append(
            f"| {escape_table_cell(segment.get('segment_id', ''))} | {escape_table_cell(time_range)} | "
            f"{escape_table_cell(segment.get('reason', ''))} | {escape_table_cell(evidence_ids)} |"
        )
    if len(lines) == 4:
        lines.append("| 없음 | 없음 | 없음 | 없음 |")
    return "\n".join(lines)


# 근거 메시지 ID에 해당하는 원본 메시지를 Markdown 표로 만든다.
def build_evidence_messages_table(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    messages_by_id = index_messages_by_id(payload.get("messages", []))
    lines = ["## 6. 주요 근거 메시지", "", "| 메시지 ID | 시간 | 작성자 | 내용 |", "|---|---|---|---|"]
    for message_id in incident.get("evidence_message_ids", []):
        message = messages_by_id.get(message_id, {})
        lines.append(
            f"| {escape_table_cell(message_id)} | {escape_table_cell(message.get('created_at', ''))} | "
            f"{escape_table_cell(message.get('sender_label', ''))} | {escape_table_cell(message.get('text', ''))} |"
        )
    if len(lines) == 4:
        lines.append("| 없음 | 없음 | 없음 | 없음 |")
    return "\n".join(lines)


# 추가 확인이 필요한 내용을 Markdown 섹션으로 만든다.
def build_missing_context_section(incident: dict[str, Any]) -> str:
    return "\n".join(["## 7. 추가 확인이 필요한 점", "", build_bullet_list(incident.get("missing_context", []))])


# 관리자가 참고할 초기 조치 목록을 Markdown 섹션으로 만든다.
def build_initial_actions_section(incident: dict[str, Any]) -> str:
    return "\n".join(["## 8. 초기 조치 참고사항", "", build_bullet_list(incident.get("recommended_initial_actions", []))])


# 자동 분석 결과의 한계를 알리는 주의 문구 섹션을 만든다.
def build_disclaimer_section(incident: dict[str, Any]) -> str:
    return "\n".join(["## 9. 주의 문구", "", incident.get("disclaimer", "")])


# Agent 분석 결과와 원본 메시지를 하나의 Notion용 Markdown 보고서로 조합한다.
def build_notion_markdown(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    sections = [
        f"# {build_notion_page_title(incident)}",
        build_notion_page_body(payload, incident),
    ]
    return "\n\n".join(sections).strip() + "\n"


# Notion 페이지 제목에 사용할 보고서 제목을 만든다.
def build_notion_page_title(incident: dict[str, Any]) -> str:
    incident_id = incident.get("incident_id", "unknown")
    return f"SilentGuard 위험 신호 알림 - {incident_id}"


# Notion 페이지 본문에 들어갈 보고서 내용을 만든다.
def build_notion_page_body(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    sections = [
        build_summary_section(payload, incident),
        build_manager_section(incident),
        build_risk_types_table(incident),
        build_risk_segments_table(incident),
        build_evidence_messages_table(payload, incident),
        build_missing_context_section(incident),
        build_initial_actions_section(incident),
        build_disclaimer_section(incident),
    ]
    return "\n\n".join(sections).strip() + "\n"


# Markdown 보고서를 지정한 경로에 저장하고 저장 경로를 반환한다.
def save_notion_markdown_report(markdown: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
