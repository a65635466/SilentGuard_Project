"""Create SilentGuard report pages with the Notion HTTP API."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai import config  # noqa: F401  Loads project-root .env.
from ai.agent_analysis.risk_segments import AgentError
from ai.notification.notion_markdown import (
    build_notion_page_title,
    build_risk_type_names,
    build_segment_risk_type,
    build_sender_labels_for_message_ids,
    format_probability_text,
    index_messages_by_id,
)


NOTION_CREATE_PAGE_URL = "https://api.notion.com/v1/pages"


# Notion API 실행에 필요한 환경변수를 읽는다.
def load_notion_config() -> dict[str, str]:
    token = os.getenv("NOTION_TOKEN", "").strip()
    parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()
    notion_version = os.getenv("NOTION_VERSION", "2026-03-11").strip()
    if not token:
        raise AgentError("NOTION_TOKEN is required")
    if not parent_page_id:
        raise AgentError("NOTION_PARENT_PAGE_ID is required")
    return {"token": token, "parent_page_id": parent_page_id, "notion_version": notion_version}


# Notion rich_text 객체를 만든다.
def build_rich_text(content: Any) -> list[dict[str, Any]]:
    return [{"type": "text", "text": {"content": str(content)}}]


# Notion heading_1 블록을 만든다.
def build_heading_1_block(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "heading_1", "heading_1": {"rich_text": build_rich_text(text)}}


# Notion heading_2 블록을 만든다.
def build_heading_2_block(text: str) -> dict[str, Any]:
    return {"object": "block", "type": "heading_2", "heading_2": {"rich_text": build_rich_text(text)}}


# Notion callout 블록을 만든다.
def build_callout_block(text: str, emoji: str = "ℹ️", color: str = "default") -> dict[str, Any]:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": build_rich_text(text),
            "icon": {"type": "emoji", "emoji": emoji},
            "color": color,
        },
    }


# Notion divider 블록을 만든다.
def build_divider_block() -> dict[str, Any]:
    return {"object": "block", "type": "divider", "divider": {}}


# Notion bullet 항목 블록을 만든다.
def build_bulleted_list_item_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": build_rich_text(text)},
    }


# Notion table_row 블록을 만든다.
def build_table_row_block(cells: list[Any]) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "table_row",
        "table_row": {"cells": [build_rich_text(cell) for cell in cells]},
    }


# Notion table 블록을 만든다.
def build_table_block(headers: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    table_rows = [build_table_row_block(headers)]
    table_rows.extend(build_table_row_block(row) for row in rows)
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows,
        },
    }


# 탐지 개요용 Notion 표 블록을 만든다.
def build_detection_overview_table_block(payload: dict[str, Any]) -> dict[str, Any]:
    return build_table_block(
        ["항목", "내용"],
        [
            ["채팅방 이름", payload.get("room_name", "")],
            ["위험 단계", payload.get("risk_level", "")],
            ["괴롭힘 위험 확률", format_probability_text(payload.get("bullying_probability", ""))],
        ],
    )


# 감지된 위험 유형용 Notion 표 블록을 만든다.
def build_risk_types_table_block(payload: dict[str, Any], incident: dict[str, Any]) -> dict[str, Any]:
    messages_by_id = index_messages_by_id(payload.get("messages", []))
    rows = []
    for risk_type in incident.get("suspected_risk_types", []):
        sender_labels = build_sender_labels_for_message_ids(
            risk_type.get("evidence_message_ids", []), messages_by_id
        )
        rows.append([risk_type.get("type", ""), sender_labels])
    if not rows:
        rows.append(["없음", "없음"])
    return build_table_block(["감지 유형", "근거 작성자"], rows)


# 위험 구간 로그용 Notion 표 블록을 만든다.
def build_risk_segments_table_block(incident: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for segment in incident.get("risk_chat_segments", []):
        time_range = f"{segment.get('start_at', '')} ~ {segment.get('end_at', '')}"
        evidence_ids = ", ".join(segment.get("evidence_message_ids", []))
        rows.append(
            [
                time_range,
                build_segment_risk_type(segment, incident),
                segment.get("reason", ""),
                evidence_ids,
            ]
        )
    if not rows:
        rows.append(["없음", "없음", "없음", "없음"])
    return build_table_block(["시간 범위", "위험 유형", "탐지 사유", "근거 메시지"], rows)


# 주요 근거 메시지용 Notion callout 블록 목록을 만든다.
def build_evidence_message_blocks(payload: dict[str, Any], incident: dict[str, Any]) -> list[dict[str, Any]]:
    messages_by_id = index_messages_by_id(payload.get("messages", []))
    blocks = []
    for message_id in incident.get("evidence_message_ids", []):
        message = messages_by_id.get(message_id, {})
        blocks.append(
            build_callout_block(
                "\n".join(
                    [
                        f"작성자: {message.get('sender_label', '')} · 시간: {message.get('created_at', '')}",
                        message.get("text", ""),
                    ]
                ),
                emoji="💬",
            )
        )
    if not blocks:
        blocks.append(build_callout_block("주요 근거 메시지가 없습니다.", emoji="💬"))
    return blocks


# 추천 조치용 Notion bullet 블록 목록을 만든다.
def build_recommended_action_blocks(incident: dict[str, Any]) -> list[dict[str, Any]]:
    actions = incident.get("recommended_initial_actions", [])
    if not actions:
        return [build_bulleted_list_item_block("없음")]
    return [build_bulleted_list_item_block(action) for action in actions]


# refined 디자인을 Notion native children 블록으로 만든다.
def build_notion_report_children(payload: dict[str, Any], incident: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        build_heading_1_block("REDPLAG"),
        build_heading_2_block("[위험 신호 알림]"),
        build_callout_block(
            "관리자가 원본 근거를 빠르게 검토할 수 있도록 구성한 Notion 보고서입니다.",
            emoji="🚩",
            color="red_background",
        ),
        build_divider_block(),
        build_heading_2_block("1. 탐지 개요"),
        build_detection_overview_table_block(payload),
        build_heading_2_block("2. 관리자 확인 내용"),
        build_callout_block(f"관리자 요약: {incident.get('manager_summary', '')}", emoji="🚩", color="red_background"),
        build_callout_block(
            f"맥락상 위험 이유: {incident.get('context_reason', '')}",
            emoji="🔎",
            color="blue_background",
        ),
        build_heading_2_block("3. 감지된 위험 유형"),
        build_risk_types_table_block(payload, incident),
        build_heading_2_block("4. 위험 구간 로그"),
        build_risk_segments_table_block(incident),
        build_heading_2_block("5. 주요 근거 메시지"),
        *build_evidence_message_blocks(payload, incident),
        build_heading_2_block("6. 추천 조치"),
        *build_recommended_action_blocks(incident),
        build_heading_2_block("7. 주의 문구"),
        build_callout_block(incident.get("disclaimer", ""), emoji="⚠️", color="red_background"),
    ]


# Notion API에 보낼 페이지 생성 요청 body를 만든다.
def build_notion_create_page_body(payload: dict[str, Any], incident: dict[str, Any], parent_page_id: str) -> dict[str, Any]:
    title = build_notion_page_title(incident)
    return {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {"title": {"title": [{"type": "text", "text": {"content": title}}]}},
        "children": build_notion_report_children(payload, incident),
    }


# Notion API 요청에 사용할 HTTP 헤더를 만든다.
def build_notion_headers(token: str, notion_version: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": notion_version,
    }


# HTTPError 응답 본문을 읽어 사람이 볼 수 있는 에러 메시지로 만든다.
def read_http_error_message(error: HTTPError) -> str:
    try:
        body = error.read().decode("utf-8")
    except UnicodeDecodeError:
        body = ""
    return f"Notion API failed with {error.code}: {body}"


# Notion HTTP API로 페이지 생성 요청을 보낸다.
def post_notion_page(request_body: dict[str, Any], config_values: dict[str, str]) -> dict[str, Any]:
    data = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    request = Request(
        NOTION_CREATE_PAGE_URL,
        data=data,
        headers=build_notion_headers(config_values["token"], config_values["notion_version"]),
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise AgentError(read_http_error_message(exc)) from exc
    except URLError as exc:
        raise AgentError(f"Notion API request failed: {exc.reason}") from exc


# Notion API 응답에서 새 페이지 URL을 꺼낸다.
def extract_notion_page_url(response: dict[str, Any]) -> str:
    notion_url = response.get("url")
    if not isinstance(notion_url, str) or not notion_url:
        raise AgentError("Notion response did not contain page url")
    return notion_url


# Agent 분석 결과와 원본 메시지를 실제 Notion 페이지로 만들고 URL을 반환한다.
def create_notion_report_page(payload: dict[str, Any], incident: dict[str, Any]) -> dict[str, Any]:
    config_values = load_notion_config()
    request_body = build_notion_create_page_body(payload, incident, config_values["parent_page_id"])
    response = post_notion_page(request_body, config_values)
    return {
        "ok": True,
        "title": build_notion_page_title(incident),
        "notion_url": extract_notion_page_url(response),
        "notion_page_id": response.get("id"),
    }
