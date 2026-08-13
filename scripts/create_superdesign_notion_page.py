"""Create a REDPLAG Notion report mockup page from the Superdesign files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_DESIGN_PATH = PROJECT_ROOT / ".superdesign" / "design-system.md"
NOTION_CREATE_PAGE_URL = "https://api.notion.com/v1/pages"


class SuperdesignNotionError(Exception):
    """Superdesign Notion page creation failed."""


# Notion rich_text 객체를 만든다.
def build_rich_text(content: Any, *, bold: bool = False, color: str = "default") -> list[dict[str, Any]]:
    return [
        {
            "type": "text",
            "text": {"content": str(content)},
            "annotations": {
                "bold": bold,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": color,
            },
        }
    ]


# Notion heading 블록을 만든다.
def build_heading_block(level: int, text: str) -> dict[str, Any]:
    block_type = f"heading_{level}"
    return {"object": "block", "type": block_type, block_type: {"rich_text": build_rich_text(text)}}


# Notion paragraph 블록을 만든다.
def build_paragraph_block(text: str, *, color: str = "default") -> dict[str, Any]:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": build_rich_text(text, color=color), "color": color},
    }


# Notion callout 블록을 만든다.
def build_callout_block(text: str, *, emoji: str, color: str = "default") -> dict[str, Any]:
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


# Notion bullet 블록을 만든다.
def build_bullet_block(text: str) -> dict[str, Any]:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": build_rich_text(text), "color": "default"},
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
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": [build_table_row_block(headers), *[build_table_row_block(row) for row in rows]],
        },
    }


# Superdesign 디자인 파일 내용을 읽는다.
def load_superdesign_design_text(design_path: Path) -> str:
    if not design_path.exists():
        raise SuperdesignNotionError(f"Superdesign design file not found: {design_path}")
    text = design_path.read_text(encoding="utf-8").strip()
    if not text:
        raise SuperdesignNotionError(f"Superdesign design file is empty: {design_path}")
    return text


# .env에서 요청된 lowercase Notion 설정을 읽는다.
def load_notion_config(env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    values = dotenv_values(env_path)
    token = (values.get("notion_api_key") or values.get("NOTION_TOKEN") or "").strip()
    parent_id = (values.get("notion_parent_id") or values.get("NOTION_PARENT_PAGE_ID") or "").strip()
    notion_version = (values.get("notion_version") or values.get("NOTION_VERSION") or "2022-06-28").strip()
    missing = [
        name
        for name, value in (
            ("notion_api_key", token),
            ("notion_parent_id", parent_id),
        )
        if not value
    ]
    if missing:
        raise SuperdesignNotionError(f"missing .env values: {', '.join(missing)}")
    return {"token": token, "parent_id": parent_id, "notion_version": notion_version}


# Superdesign 목업의 샘플 보고서 데이터를 만든다.
def build_report_mockup_data() -> dict[str, Any]:
    return {
        "room_name": "1학년 3반 단체방",
        "risk_level": "immediate",
        "probability": "91%",
        "manager_summary": "원본 대화에서 배제와 압박의 위험 신호가 확인되어 관리자 검토가 필요합니다.",
        "context_reason": "특정 참여자를 향한 조롱성 표현과 배제 표현이 짧은 시간 안에 반복되었습니다.",
        "risk_types": [["배제성", "A"], ["조롱/비하", "A"]],
        "segments": [
            [
                "2026-08-08 14:28 ~ 14:31",
                "배제성, 조롱/비하",
                "특정 참여자에게 대화 참여를 막는 표현이 이어짐",
                "msg_001, msg_003",
            ]
        ],
        "evidence": [
            ["A", "2026-08-08 14:28", "너 왜 또 여기 들어왔냐"],
            ["A", "2026-08-08 14:30", "아무도 너랑 말하기 싫대"],
        ],
        "actions": [
            "원본 대화 전체를 먼저 확인하고 자동 분석 결과를 참고 자료로만 사용합니다.",
            "관련 학생 또는 참여자와 개별 면담 일정을 잡습니다.",
            "반복 여부를 확인하기 위해 같은 채팅방의 이전 대화 흐름을 검토합니다.",
        ],
        "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
    }


# Superdesign 디자인 기준을 반영한 Notion children 블록을 만든다.
def build_report_children(design_text: str) -> list[dict[str, Any]]:
    report = build_report_mockup_data()
    return [
        build_heading_block(1, "REDPLAG"),
        build_heading_block(2, "[위험 신호 알림]"),
        build_callout_block(
            "관리자가 원본 근거를 빠르게 검토할 수 있도록 구성한 Notion 보고서 목업입니다.",
            emoji="🚩",
            color="red_background",
        ),
        build_divider_block(),
        build_heading_block(2, "1. 탐지 개요"),
        build_table_block(
            ["항목", "내용"],
            [
                ["채팅방 이름", report["room_name"]],
                ["위험 단계", report["risk_level"]],
                ["괴롭힘 위험 확률", report["probability"]],
            ],
        ),
        build_heading_block(2, "2. 관리자 확인 내용"),
        build_callout_block(f"관리자 요약: {report['manager_summary']}", emoji="🔎", color="blue_background"),
        build_callout_block(f"맥락상 위험 이유: {report['context_reason']}", emoji="ℹ️", color="gray_background"),
        build_heading_block(2, "3. 감지된 위험 유형"),
        build_table_block(["감지 유형", "근거 작성자"], report["risk_types"]),
        build_heading_block(2, "4. 위험 구간 로그"),
        build_table_block(["시간 범위", "위험 유형", "탐지 사유", "근거 메시지"], report["segments"]),
        build_heading_block(2, "5. 주요 근거 메시지"),
        build_table_block(["작성자", "채팅 시간", "원본 메시지"], report["evidence"]),
        build_heading_block(2, "6. 추천 조치"),
        *[build_bullet_block(action) for action in report["actions"]],
        build_heading_block(2, "7. 주의 문구"),
        build_callout_block(report["disclaimer"], emoji="⚠️", color="red_background"),
        build_heading_block(3, "디자인 기준"),
        build_paragraph_block(extract_design_principle_summary(design_text), color="gray"),
    ]


# Superdesign 디자인 원칙 요약 문장을 뽑는다.
def extract_design_principle_summary(design_text: str) -> str:
    for line in design_text.splitlines():
        cleaned = line.strip()
        if cleaned.startswith("- Tone:"):
            return cleaned.removeprefix("- ").strip()
    return "Tone: serious, calm, administrative, evidence-first."


# Notion 페이지 생성 요청 body를 만든다.
def build_superdesign_notion_page_body(design_path: Path, parent_id: str) -> dict[str, Any]:
    design_text = load_superdesign_design_text(design_path)
    return {
        "parent": {"type": "page_id", "page_id": parent_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": "REDPLAG [위험 신호 알림]"}}]
            }
        },
        "children": build_report_children(design_text),
    }


# Notion API 요청 헤더를 만든다.
def build_notion_headers(config_values: dict[str, str]) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config_values['token']}",
        "Content-Type": "application/json",
        "Notion-Version": config_values["notion_version"],
    }


# Notion API 오류 응답을 읽기 쉬운 예외 메시지로 바꾼다.
def read_http_error_message(error: HTTPError) -> str:
    try:
        body = error.read().decode("utf-8")
    except UnicodeDecodeError:
        body = ""
    return f"Notion API failed with {error.code}: {body}"


# Superdesign 목업 페이지를 Notion API로 생성한다.
def create_superdesign_notion_page(
    design_path: Path,
    config_values: dict[str, str],
    *,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, str]:
    request_body = build_superdesign_notion_page_body(design_path, config_values["parent_id"])
    request = Request(
        NOTION_CREATE_PAGE_URL,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers=build_notion_headers(config_values),
        method="POST",
    )
    try:
        with opener(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise SuperdesignNotionError(read_http_error_message(exc)) from exc
    except URLError as exc:
        raise SuperdesignNotionError(f"Notion API request failed: {exc.reason}") from exc
    return {"page_id": result.get("id", ""), "url": result.get("url", "")}


# CLI 인자를 파싱한다.
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a REDPLAG Superdesign mockup page in Notion.")
    parser.add_argument("--env", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN_PATH)
    return parser.parse_args()


# CLI 실행 진입점을 처리한다.
def main() -> None:
    args = parse_args()
    config_values = load_notion_config(args.env)
    result = create_superdesign_notion_page(args.design, config_values)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
