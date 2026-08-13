"""Run Phase 5 and create a real Notion report page."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .notion_delivery import create_notion_report_page
from .risk_segments import AgentError
from .run_phase_04 import load_json_file


# Phase 5 입력 파일을 받아 실제 Notion 페이지를 생성한다.
def run_phase_05(input_file: Path, incident_file: Path) -> dict:
    payload = load_json_file(input_file)
    incident = load_json_file(incident_file)
    return create_notion_report_page(payload, incident)


# 명령행 인자를 받아 Phase 5 실행 함수를 호출한다.
def main() -> int:
    parser = argparse.ArgumentParser(description="Create a SilentGuard report page in Notion")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("incident_file", type=Path)
    args = parser.parse_args()
    try:
        result = run_phase_05(args.input_file, args.incident_file)
    except (OSError, json.JSONDecodeError, AgentError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
