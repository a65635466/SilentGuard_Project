"""Create SilentGuard report pages with the Notion HTTP API."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import config  # noqa: F401  Loads project-root .env.
from .notion_markdown import build_notion_page_body, build_notion_page_title
from .risk_segments import AgentError


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


# Notion API에 보낼 페이지 생성 요청 body를 만든다.
def build_notion_create_page_body(payload: dict[str, Any], incident: dict[str, Any], parent_page_id: str) -> dict[str, Any]:
    title = build_notion_page_title(incident)
    body = build_notion_page_body(payload, incident)
    return {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {"title": {"title": [{"type": "text", "text": {"content": title}}]}},
        "markdown": body,
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
