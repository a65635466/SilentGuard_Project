"""Run Phase 4 and create a local Notion Markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .notion_markdown import build_notion_markdown, save_notion_markdown_report


# JSON 파일을 읽어 Python dict로 변환한다.
def load_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# Phase 4 입력 파일을 받아 Notion Markdown 보고서를 생성한다.
def run_phase_04(input_file: Path, incident_file: Path, output_file: Path) -> Path:
    payload = load_json_file(input_file)
    incident = load_json_file(incident_file)
    markdown = build_notion_markdown(payload, incident)
    return save_notion_markdown_report(markdown, output_file)


# 명령행 인자를 받아 Phase 4 실행 함수를 호출한다.
def main() -> int:
    parser = argparse.ArgumentParser(description="Create a SilentGuard Notion Markdown report")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("incident_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("app/output/notion_report.md"))
    args = parser.parse_args()
    output_path = run_phase_04(args.input_file, args.incident_file, args.output)
    print(f"created: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
