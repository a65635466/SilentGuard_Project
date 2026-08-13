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


# 위험 확률을 관리자 표시용 퍼센트로 바꾼다.
def format_probability_text(probability: Any) -> str:
    if isinstance(probability, (int, float)):
        value = float(probability)
        if 0 <= value <= 1:
            return f"{round(value * 100)}%"
        return f"{round(value)}%"
    return str(probability) if probability else "-"


# 보고서 상단의 탐지 개요 섹션을 만든다.
def build_detection_overview_section(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    probability = payload.get("bullying_probability", "")
    lines = [
        "## 1. 탐지 개요",
        "",
        "| 항목 | 내용 |",
        "|---|---|",
        f"| 채팅방 이름 | {escape_table_cell(payload.get('room_name', ''))} |",
        f"| 위험 단계 | {escape_table_cell(payload.get('risk_level', ''))} |",
        f"| 괴롭힘 위험 확률 | {escape_table_cell(format_probability_text(probability))} |",
    ]
    return "\n".join(lines)


# 관리자가 먼저 읽을 요약과 맥락 설명 섹션을 만든다.
def build_manager_section(incident: dict[str, Any]) -> str:
    lines = [
        "## 2. 관리자 확인 내용",
        "",
        f"> **관리자 요약:** {incident.get('manager_summary', '')}",
    ]
    context_reason = incident.get("context_reason", "")
    if context_reason:
        lines.extend(["", f"> **맥락상 위험 이유:** {context_reason}"])
    return "\n".join(lines)


# 메시지 ID 목록을 원본 메시지의 작성자 목록으로 바꾼다.
def build_sender_labels_for_message_ids(
    message_ids: list[str], messages_by_id: dict[str, dict[str, Any]]
) -> str:
    sender_labels = []
    for message_id in message_ids:
        message = messages_by_id.get(message_id, {})
        sender_labels.append(message.get("sender_label") or message.get("sender_id") or "알 수 없음")
    return ", ".join(sender_labels)


# 의심 위험 유형을 Markdown 표로 만든다.
def build_risk_types_table(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    messages_by_id = index_messages_by_id(payload.get("messages", []))
    lines = ["## 3. 감지된 위험 유형", "", "| 감지 유형 | 근거 작성자 |", "|---|---|"]
    for risk_type in incident.get("suspected_risk_types", []):
        sender_labels = build_sender_labels_for_message_ids(
            risk_type.get("evidence_message_ids", []), messages_by_id
        )
        lines.append(f"| {escape_table_cell(risk_type.get('type', ''))} | {escape_table_cell(sender_labels)} |")
    if len(lines) == 4:
        lines.append("| 없음 | 없음 |")
    return "\n".join(lines)


# Agent 결과의 위험 유형 이름을 하나의 표시 문구로 만든다.
def build_risk_type_names(incident: dict[str, Any]) -> str:
    names = [
        risk_type.get("type", "")
        for risk_type in incident.get("suspected_risk_types", [])
        if risk_type.get("type")
    ]
    return ", ".join(names) if names else "-"


# 위험 구간 하나에 표시할 위험 유형을 고른다.
def build_segment_risk_type(segment: dict[str, Any], incident: dict[str, Any]) -> str:
    if segment.get("risk_type"):
        return str(segment["risk_type"])
    if segment.get("type"):
        return str(segment["type"])
    risk_types = segment.get("risk_types")
    if isinstance(risk_types, list) and risk_types:
        return ", ".join(str(risk_type) for risk_type in risk_types)
    return build_risk_type_names(incident)


# Agent가 잡은 위험 구간을 Markdown 표로 만든다.
def build_risk_segments_table(incident: dict[str, Any]) -> str:
    lines = [
        "## 4. 위험 구간 로그",
        "",
        "| 시간 범위 | 위험 유형 | 탐지 사유 | 근거 메시지 |",
        "|---|---|---|---|",
    ]
    for segment in incident.get("risk_chat_segments", []):
        time_range = f"{segment.get('start_at', '')} ~ {segment.get('end_at', '')}"
        risk_type = build_segment_risk_type(segment, incident)
        evidence_ids = ", ".join(segment.get("evidence_message_ids", []))
        lines.append(
            f"| {escape_table_cell(time_range)} | {escape_table_cell(risk_type)} | "
            f"{escape_table_cell(segment.get('reason', ''))} | {escape_table_cell(evidence_ids)} |"
        )
    if len(lines) == 4:
        lines.append("| 없음 | 없음 | 없음 | 없음 |")
    return "\n".join(lines)


# 근거 메시지 ID에 해당하는 원본 메시지를 Markdown 카드형 블록으로 만든다.
def build_evidence_messages_section(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    messages_by_id = index_messages_by_id(payload.get("messages", []))
    lines = ["## 5. 주요 근거 메시지", ""]
    for message_id in incident.get("evidence_message_ids", []):
        message = messages_by_id.get(message_id, {})
        sender_label = message.get("sender_label", "")
        created_at = message.get("created_at", "")
        text = message.get("text", "")
        lines.extend(
            [
                f"> **작성자:** {sender_label} · **시간:** {created_at}",
                f"> {text}",
                "",
            ]
        )
    if len(lines) == 2:
        lines.append("- 없음")
    return "\n".join(lines)


# 추가 확인이 필요한 내용을 Markdown 섹션으로 만든다.
def build_missing_context_section(incident: dict[str, Any]) -> str:
    return "\n".join(["## 7. 추가 확인이 필요한 점", "", build_bullet_list(incident.get("missing_context", []))])


# 관리자가 참고할 추천 조치 목록을 Markdown 섹션으로 만든다.
def build_recommended_actions_section(incident: dict[str, Any]) -> str:
    return "\n".join(["## 6. 추천 조치", "", build_bullet_list(incident.get("recommended_initial_actions", []))])


# 자동 분석 결과의 한계를 알리는 주의 문구 섹션을 만든다.
def build_disclaimer_section(incident: dict[str, Any]) -> str:
    return "\n".join(["## 7. 주의 문구", "", f"> {incident.get('disclaimer', '')}"])


# Agent 분석 결과와 원본 메시지를 하나의 Notion용 Markdown 보고서로 조합한다.
def build_notion_markdown(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    sections = [
        f"# {build_notion_page_title(incident)}",
        build_notion_page_body(payload, incident),
    ]
    return "\n\n".join(sections).strip() + "\n"


# Notion 페이지 제목에 사용할 보고서 제목을 만든다.
def build_notion_page_title(incident: dict[str, Any]) -> str:
    return "REDPLAG\n[위험 신호 알림]"


# Notion 페이지 본문에 들어갈 보고서 내용을 만든다.
def build_notion_page_body(payload: dict[str, Any], incident: dict[str, Any]) -> str:
    sections = [
        build_detection_overview_section(payload, incident),
        build_manager_section(incident),
        build_risk_types_table(payload, incident),
        build_risk_segments_table(incident),
        build_evidence_messages_section(payload, incident),
        build_recommended_actions_section(incident),
        build_disclaimer_section(incident),
    ]
    return "\n\n".join(sections).strip() + "\n"


# Markdown 보고서를 지정한 경로에 저장하고 저장 경로를 반환한다.
def save_notion_markdown_report(markdown: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
